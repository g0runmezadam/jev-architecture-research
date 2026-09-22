"""Black-box probes for Jev/Laya decision-model behavior."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import time
from types import SimpleNamespace
from pathlib import Path

from harness.judge.base import to_plain
from harness.judge.http import HttpJudge

ROOT = Path(__file__).resolve().parents[1]


def entropy(probs: dict) -> float:
    return -sum(float(p) * math.log2(float(p)) for p in probs.values() if float(p) > 0)


def call(judge: HttpJudge, state, questions) -> dict:
    t0 = time.perf_counter()
    response = judge.system_one(state, questions)
    raw_answers = response.answers
    answers = raw_answers if isinstance(raw_answers, dict) and all(isinstance(v, dict) for v in raw_answers.values()) else to_plain(raw_answers)
    return {"ms": (time.perf_counter() - t0) * 1000, "cached": response.cached, "model": response.model, "answers": answers, "input_tokens": response.input_tokens, "output_tokens": response.output_tokens}


class LocalLayaJudge:
    def __init__(self, subfolder: str, model: str):
        import laya
        self.agent = laya.load("convaiinnovations/laya", subfolder=subfolder or None)
        self.model = model

    def system_one(self, state, questions):
        result = self.agent.predict(state, questions)
        return SimpleNamespace(model=self.model, answers=result["answers"], cached=False, input_tokens=result.get("usage", {}).get("input_tokens", 0), output_tokens=0)


def label_permutation(judge: HttpJudge) -> list[dict]:
    state = "The customer was charged twice for the same invoice and requests a refund."
    permutations = [
        ["billing", "technical", "sales"],
        ["sales", "billing", "technical"],
        ["technical", "sales", "billing"],
        ["banana", "billing", "spaceship"],
        ["x9", "q4", "billing"],
    ]
    rows = []
    for i, labels in enumerate(permutations):
        criteria = {label: {"what": "Handles duplicate charges, invoices and refunds" if label == "billing" else "Unrelated department", "examples": ["duplicate invoice"] if label == "billing" else ["unrelated request"]} for label in labels}
        result = call(judge, state + f" (permutation {i})", {"route": {"type": "choice", "instructions": "Which department should handle this request?", "criteria": criteria}})
        answer = result["answers"]["route"]
        rows.append({"order": labels, "choice": answer.get("choice"), "probabilities": answer.get("probabilities", {}), "confidence": answer.get("confidence"), **{k: result[k] for k in ("ms", "cached", "input_tokens")}})
    return rows


def cardinality(judge: HttpJudge) -> list[dict]:
    rows = []
    for n in (3, 5, 10, 20, 50, 75, 100, 150, 200, 255):
        labels = ["billing"] + [f"decoy_{i:03d}" for i in range(n - 1)]
        criteria = {label: ("Payments, duplicate charges and refunds" if label == "billing" else f"Unrelated category {label}") for label in labels}
        try:
            result = call(judge, f"The customer was charged twice and wants the duplicate payment refunded. (N={n})", {"route": {"type": "choice", "instructions": "Which category best matches this request?", "criteria": criteria}})
        except Exception as exc:
            rows.append({"n_options": n, "error": f"{type(exc).__name__}: {exc}"})
            continue
        answer = result["answers"]["route"]
        probs = answer.get("probabilities", {})
        rows.append({"n_options": n, "choice": answer.get("choice"), "correct_probability": probs.get("billing"), "confidence": answer.get("confidence"), "entropy_bits": entropy(probs), **{k: result[k] for k in ("ms", "cached", "input_tokens")}})
    return rows


def noul_inversion(judge: HttpJudge) -> list[dict]:
    rows = []
    for i, state in enumerate([
        "The customer explicitly asks for a refund after being charged twice.",
        "The customer says the charge is correct and does not want a refund.",
        "The customer asks how to update their profile name and says nothing about money.",
        "Müşteri iki kez ücretlendirildiğini ve para iadesi istediğini söylüyor.",
    ]):
        result = call(judge, state + f" (inversion {i})", {
            "positive": {"type": "noul", "instructions": "Is the customer requesting a refund?"},
            "negative": {"type": "noul", "instructions": "Is the customer explicitly not requesting a refund?"},
        })
        p = {key: float(value.get("noul", 0.5)) for key, value in result["answers"].items()}
        rows.append({"state": state, "p_positive": p["positive"], "p_negative": p["negative"], "sum": p["positive"] + p["negative"], "deviation_from_one": abs(p["positive"] + p["negative"] - 1), **{k: result[k] for k in ("ms", "cached", "input_tokens")}})
    return rows


def question_scaling(judge: HttpJudge) -> list[dict]:
    rows = []
    state = "The customer was charged twice for an invoice and wants the duplicate payment refunded."
    for n in (1, 2, 5, 10, 20, 50, 100):
        questions = {f"q{i:03d}": {"type": "choice", "instructions": f"Which department should handle this duplicate-charge request? Wording variant {i}.", "criteria": {"billing": "Invoices, payments and refunds", "technical": "Bugs and API errors", "sales": "Plans and contracts"}} for i in range(n)}
        result = call(judge, state + f" (question batch {n})", questions)
        correct = sum(value.get("choice") == "billing" for value in result["answers"].values())
        rows.append({"n_questions": n, "correct": correct, "accuracy": correct / n, "response_answers": len(result["answers"]), "ms": result["ms"], "ms_per_question": result["ms"] / n, "cached": result["cached"], "input_tokens": result["input_tokens"], "output_tokens": result["output_tokens"]})
    return rows


def decoys(judge: HttpJudge) -> list[dict]:
    rows = []
    for n in (3, 5, 10, 20, 50, 100, 200):
        labels = ["billing"] + [f"nonsense_{i:03d}" for i in range(n - 1)]
        criteria = {label: ("Handles duplicate charges and refunds" if label == "billing" else "An unrelated random category with no relation to payments") for label in labels}
        try:
            result = call(judge, f"Duplicate invoice charge; the customer requests a refund. (decoys={n})", {"route": {"type": "choice", "instructions": "Which category is correct?", "criteria": criteria}})
        except Exception as exc:
            rows.append({"n_options": n, "error": f"{type(exc).__name__}: {exc}"})
            continue
        answer = result["answers"]["route"]
        probs = answer.get("probabilities", {})
        rows.append({"n_options": n, "choice": answer.get("choice"), "correct_probability": probs.get("billing"), "confidence": answer.get("confidence"), "entropy_bits": entropy(probs), **{k: result[k] for k in ("ms", "cached", "input_tokens")}})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--laya-url", default="http://127.0.0.1:8100")
    parser.add_argument("--laya-model", default="laya-multilingual")
    parser.add_argument("--out", default="results/architecture-probes.json")
    parser.add_argument("--only", default="all", help="comma-separated: permutation,cardinality,inversion,scaling,decoys")
    parser.add_argument("--direct-laya", action="store_true", help="load Laya in this process instead of using the HTTP shim")
    args = parser.parse_args()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    laya_judge = LocalLayaJudge("multilingual" if args.laya_model == "laya-multilingual" else ("typed-decisions" if "typed" in args.laya_model else None), args.laya_model) if args.direct_laya else HttpJudge(args.laya_url, "", args.laya_model, cache_dir=ROOT / "json_cache" / f"probe-laya-{stamp}")
    judges = {
        args.laya_model: laya_judge,
        "jev-1.13.0": HttpJudge("https://api.typesafe.ai", os.environ.get("TYPESAFE_API_KEY", ""), "jev-1.13.0", cache_dir=ROOT / "json_cache" / f"probe-jev-{stamp}"),
    }
    selected = {"permutation", "cardinality", "inversion", "scaling", "decoys"} if args.only == "all" else set(args.only.split(","))
    output = {"created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "experiments": {}, "selected": sorted(selected)}
    for name, judge in judges.items():
        print(f"running probes for {name}", flush=True)
        output["experiments"][name] = {}
        if "permutation" in selected:
            output["experiments"][name]["label_permutation"] = label_permutation(judge)
        if "cardinality" in selected:
            output["experiments"][name]["cardinality"] = cardinality(judge)
        if "inversion" in selected:
            output["experiments"][name]["noul_inversion"] = noul_inversion(judge)
        if "scaling" in selected:
            output["experiments"][name]["question_scaling"] = question_scaling(judge)
        if "decoys" in selected:
            output["experiments"][name]["decoy_injection"] = decoys(judge)
        print(json.dumps({k: len(v) for k, v in output["experiments"][name].items()}))
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {out}")


if __name__ == "__main__":
    raise SystemExit(main())
