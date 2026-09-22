"""Score/ordinal and determinism probes for Jev versus Laya."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from pathlib import Path
from types import SimpleNamespace

from harness.judge.base import to_plain
from harness.judge.http import HttpJudge

ROOT = Path(__file__).resolve().parents[1]


class LocalLayaJudge:
    def __init__(self, model: str):
        import laya
        subfolder = "multilingual" if model == "laya-multilingual" else ("typed-decisions" if "typed" in model else None)
        self.agent = laya.load("convaiinnovations/laya", subfolder=subfolder)
        self.model = model

    def system_one(self, state, questions):
        result = self.agent.predict(state, questions)
        return SimpleNamespace(model=self.model, answers=result["answers"], cached=False, input_tokens=result.get("usage", {}).get("input_tokens", 0), output_tokens=0)


def ask(judge, state, questions):
    t0 = time.perf_counter()
    response = judge.system_one(state, questions)
    answers = response.answers if isinstance(response.answers, dict) and all(isinstance(v, dict) for v in response.answers.values()) else to_plain(response.answers)
    return {"answers": answers, "ms": (time.perf_counter() - t0) * 1000, "cached": response.cached, "input_tokens": response.input_tokens, "output_tokens": response.output_tokens, "model": response.model}


def sweep(judge):
    rows = []
    state = "The production service is completely unavailable for every customer and there is no workaround."
    for n in (2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 50, 75, 100):
        criteria = [{"what": f"Severity level {i}: " + ("minor cosmetic issue" if i == 0 else "complete outage and data loss" if i == n - 1 else f"intermediate operational impact {i}"), "examples": [f"example for level {i}"]} for i in range(n)]
        try:
            result = ask(judge, f"{state} (levels={n})", {"severity": {"type": "score", "instructions": "What severity level best describes this incident?", "criteria": criteria}})
        except Exception as exc:
            rows.append({"levels": n, "error": f"{type(exc).__name__}: {exc}"})
            continue
        answer = result["answers"]["severity"]
        probs = {str(k): float(v) for k, v in (answer.get("probabilities") or {}).items()}
        expected = sum(float(k) * v for k, v in probs.items()) if probs else None
        variance = sum(((float(k) - expected) ** 2) * v for k, v in probs.items()) if expected is not None else None
        rows.append({"levels": n, "score": answer.get("score"), "expected_from_probabilities": expected, "difference": None if expected is None else float(answer.get("score", 0)) - expected, "variance_from_probabilities": variance, "confidence": answer.get("confidence"), "probabilities": probs, "legend": answer.get("legend"), **{k: result[k] for k in ("ms", "cached", "input_tokens")}})
    return rows


def inversion(judge):
    state = "The payment service is down for every customer and orders are being lost."
    normal = [
        {"what": "Minor: cosmetic issue, nothing is broken", "examples": ["typo"]},
        {"what": "Moderate: feature is degraded but workaround exists", "examples": ["one browser fails"]},
        {"what": "Critical: complete outage, no workaround, or data loss", "examples": ["nobody can log in"]},
    ]
    reversed_levels = list(reversed(normal))
    rows = []
    for name, criteria in (("normal", normal), ("reversed", reversed_levels)):
        result = ask(judge, state + f" (order={name})", {"severity": {"type": "score", "instructions": "What severity level best describes this incident?", "criteria": criteria}})
        rows.append({"order": name, "answer": result["answers"]["severity"], **{k: result[k] for k in ("ms", "cached", "input_tokens")}})
    return rows


def deterministic(judge_factory, repeats: int):
    state = "The user requests a refund for a duplicate charge."
    questions = {"route": {"type": "choice", "instructions": "Which department should handle this?", "criteria": {"billing": "payments and refunds", "technical": "bugs and outages", "sales": "plans and contracts"}}}
    rows = []
    for i in range(repeats):
        judge = judge_factory(i)
        result = ask(judge, state, questions)
        rows.append({"choice": result["answers"]["route"].get("choice"), "probabilities": result["answers"]["route"].get("probabilities", {}), "confidence": result["answers"]["route"].get("confidence"), "ms": result["ms"], "cached": result["cached"]})
    baseline = rows[0]
    max_probability_delta = max(max(abs(float(row["probabilities"].get(k, 0)) - float(baseline["probabilities"].get(k, 0))) for k in set(row["probabilities"]) | set(baseline["probabilities"])) for row in rows[1:]) if len(rows) > 1 else 0
    return {"repeats": repeats, "choices": sorted(set(row["choice"] for row in rows)), "max_probability_delta": max_probability_delta, "confidence_values": sorted(set(row["confidence"] for row in rows)), "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=30)
    parser.add_argument("--out", default="results/score-probes.json")
    args = parser.parse_args()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    laya_model = "laya-multilingual"
    judges = {
        laya_model: LocalLayaJudge(laya_model),
        "jev-1.13.0": HttpJudge("https://api.typesafe.ai", os.environ.get("TYPESAFE_API_KEY", ""), "jev-1.13.0", cache_dir=ROOT / "json_cache" / f"score-jev-{stamp}"),
    }
    result = {"created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "summary": {}, "detail": {}}
    for name, judge in judges.items():
        print(f"running {name}", flush=True)
        result["detail"][name] = {"sweep": sweep(judge), "inversion": inversion(judge)}
        if name.startswith("laya"):
            factory = lambda i, existing=judge: existing
        else:
            factory = lambda i: HttpJudge("https://api.typesafe.ai", os.environ.get("TYPESAFE_API_KEY", ""), "jev-1.13.0", cache_dir=ROOT / "json_cache" / f"det-jev-{stamp}-{i}")
        result["detail"][name]["determinism"] = deterministic(factory, args.repeats)
        print(f"{name}: sweep={len(result['detail'][name]['sweep'])}, deterministic_delta={result['detail'][name]['determinism']['max_probability_delta']}")
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {out}")


if __name__ == "__main__":
    raise SystemExit(main())
