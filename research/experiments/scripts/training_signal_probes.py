"""Behavioral probes for latent features, contradictions and evidence accumulation."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from types import SimpleNamespace

from harness.judge.base import to_plain
from harness.judge.http import HttpJudge

ROOT = Path(__file__).resolve().parents[1]


class LocalLayaJudge:
    def __init__(self):
        import laya
        self.agent = laya.load("convaiinnovations/laya", subfolder="multilingual")
        self.model = "laya-multilingual"

    def system_one(self, state, questions):
        result = self.agent.predict(state, questions)
        return SimpleNamespace(model=self.model, answers=result["answers"], cached=False, input_tokens=result.get("usage", {}).get("input_tokens", 0), output_tokens=0)


def ask(judge, state, questions):
    started = time.perf_counter()
    response = judge.system_one(state, questions)
    answers = response.answers if isinstance(response.answers, dict) and all(isinstance(v, dict) for v in response.answers.values()) else to_plain(response.answers)
    return {"answers": answers, "ms": (time.perf_counter() - started) * 1000, "cached": response.cached, "input_tokens": response.input_tokens, "model": response.model}


def counterfactual(judge):
    base = {"issue": "billing", "urgency": "low", "fraud": False, "language": "English"}
    variants = [
        ("base", base),
        ("technical", {**base, "issue": "technical"}),
        ("urgent", {**base, "urgency": "high"}),
        ("fraud", {**base, "fraud": True}),
        ("turkish", {**base, "language": "Turkish"}),
    ]
    q = {
        "billing": {"type": "noul", "instructions": "Does this require billing support?"},
        "urgent": {"type": "noul", "instructions": "Is this urgent?"},
        "fraud": {"type": "noul", "instructions": "Is fraud involved?"},
    }
    rows = []
    for name, state in variants:
        result = ask(judge, {"state": state}, q)
        rows.append({"variant": name, "state": state, "answers": result["answers"], "ms": result["ms"]})
    return rows


def orthogonal(judge):
    features = [
        ("billing", {"billing": True, "urgent": False, "fraud": False, "sentiment": "calm"}),
        ("urgent", {"billing": False, "urgent": True, "fraud": False, "sentiment": "calm"}),
        ("fraud", {"billing": False, "urgent": False, "fraud": True, "sentiment": "calm"}),
        ("angry", {"billing": False, "urgent": False, "fraud": False, "sentiment": "angry"}),
        ("all", {"billing": True, "urgent": True, "fraud": True, "sentiment": "angry"}),
    ]
    q = {
        "billing": {"type": "noul", "instructions": "Does this require billing support?"},
        "urgent": {"type": "noul", "instructions": "Is this urgent?"},
        "fraud": {"type": "noul", "instructions": "Is fraud involved?"},
        "angry": {"type": "noul", "instructions": "Is the customer angry?"},
    }
    rows = []
    for name, state in features:
        result = ask(judge, {"state": state}, q)
        rows.append({"variant": name, "answers": result["answers"], "ms": result["ms"]})
    return rows


def contradiction(judge):
    states = [
        ("customer_yes_metadata_no", {"customer": "I want a refund for the duplicate charge.", "metadata": {"refund_requested": False}}),
        ("customer_no_metadata_yes", {"customer": "I do not want a refund; the charge is correct.", "metadata": {"refund_requested": True}}),
        ("both_yes", {"customer": "Please refund the duplicate charge.", "metadata": {"refund_requested": True}}),
        ("both_no", {"customer": "Please explain the invoice; no refund is requested.", "metadata": {"refund_requested": False}}),
    ]
    q = {"refund": {"type": "noul", "instructions": "Is the customer requesting a refund?"}}
    rows = []
    for name, state in states:
        result = ask(judge, state, q)
        rows.append({"case": name, "state": state, "answer": result["answers"]["refund"], "ms": result["ms"]})
    return rows


def evidence(judge):
    rows = []
    for n in (1, 2, 5, 10, 20):
        snippets = [f"Evidence {i}: the customer was charged twice and explicitly requests a refund." for i in range(n)]
        state = {"question": "Does the customer request a refund?", "evidence": snippets}
        q = {"refund": {"type": "noul", "instructions": "Does the customer request a refund?"}}
        result = ask(judge, state, q)
        answer = result["answers"]["refund"]
        rows.append({"n_evidence": n, "p_true": answer.get("noul"), "ms": result["ms"], "input_tokens": result["input_tokens"]})
    return rows


def semantic_options(judge):
    options = {"billing": "payments and refunds", "invoice": "invoices and billing documents", "payment_issue": "a problem with a payment transaction", "subscription": "subscription plans and cancellation", "accounting": "accounting and bookkeeping"}
    states = [
        ("duplicate_charge", "I was charged twice for the same payment and need the duplicate refunded."),
        ("invoice_copy", "Please send me a copy of last month's invoice."),
        ("cancel_plan", "I want to cancel my subscription immediately."),
        ("bookkeeping", "Our accountant needs the ledger export for reconciliation."),
        ("card_failed", "My card payment failed at checkout.")
    ]
    rows = []
    for name, state in states:
        result = ask(judge, state, {"route": {"type": "choice", "instructions": "Which category best matches this request?", "criteria": options}})
        rows.append({"case": name, "state": state, "answer": result["answers"]["route"], "ms": result["ms"]})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results/training-signal-probes.json")
    args = parser.parse_args()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    judges = {
        "laya-multilingual": LocalLayaJudge(),
        "jev-1.13.0": HttpJudge("https://api.typesafe.ai", os.environ.get("TYPESAFE_API_KEY", ""), "jev-1.13.0", cache_dir=ROOT / "json_cache" / f"training-jev-{stamp}"),
    }
    result = {"created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "experiments": {}}
    for name, judge in judges.items():
        print(f"running {name}", flush=True)
        result["experiments"][name] = {
            "counterfactual": counterfactual(judge),
            "orthogonal": orthogonal(judge),
            "contradiction": contradiction(judge),
            "evidence_accumulation": evidence(judge),
            "semantic_options": semantic_options(judge),
        }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {out}")


if __name__ == "__main__":
    raise SystemExit(main())
