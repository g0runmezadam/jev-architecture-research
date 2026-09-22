"""Targeted Jev probes for candidate reduction and failure-surface research.

This script records black-box behavior only. It does not train on provider output.
"""
from __future__ import annotations

import argparse, json, math, os, statistics, time
from pathlib import Path
from harness.judge.http import HttpJudge
from harness.judge.base import to_plain

ROOT = Path(__file__).resolve().parents[1]

def entropy(p):
    return -sum(float(v) * math.log2(float(v)) for v in p.values() if float(v) > 0)

def run(judge, state, question, meta):
    t = time.perf_counter()
    try:
        r = judge.system_one(state, {"route": question})
        a = to_plain(r.answers)["route"]
        probs = a.get("probabilities", {})
        return {**meta, "ok": True, "ms": round((time.perf_counter()-t)*1000, 2),
                "choice": a.get("choice"), "confidence": a.get("confidence"),
                "probabilities": probs, "entropy_bits": round(entropy(probs), 6),
                "cached": r.cached, "input_tokens": r.input_tokens}
    except Exception as e:
        return {**meta, "ok": False, "ms": round((time.perf_counter()-t)*1000, 2),
                "error": f"{type(e).__name__}: {e}"}

def question(options, instruction="Which category best matches the request?"):
    return {"type":"choice", "instructions":instruction,
            "criteria": {k:v for k,v in options}}

def candidate_probes(judge):
    rows=[]
    state="The customer was charged twice for the same invoice and wants the duplicate payment refunded."
    near=[("billing","Invoices, payments, duplicate charges and refunds"),
          ("payment_issue","Payment was duplicated or charged incorrectly"),
          ("refund","A customer requests money back for a transaction"),
          ("invoice","Questions about invoices and billing documents"),
          ("subscription","Plans, renewals and recurring subscriptions"),
          ("technical","Bugs, outages and API errors")]
    unrelated=[(f"decoy_{i:03d}", f"Unrelated category number {i}") for i in range(1, 251)]
    for density in (0,1,3,10,25,50,100,200):
        for position in ("first","middle","last"):
            options=list(near[:density if density < len(near) else len(near)]) if density else list(near[:1])
            if density > len(near):
                options = list(near) + unrelated[:density-len(near)]
            target = [x for x in options if x[0]=="billing"][0]
            rest=[x for x in options if x[0]!="billing"]
            if position=="first": ordered=[target]+rest
            elif position=="last": ordered=rest+[target]
            else:
                mid=len(rest)//2; ordered=rest[:mid]+[target]+rest[mid:]
            rows.append(run(judge,state,question(ordered),{"experiment":"candidate_density","density":density,"position":position,"option_count":len(ordered),"target":"billing"}))
    return rows

def failure_probes(judge):
    rows=[]
    base={"billing":"Billing, invoices and payments","technical":"Technical bugs and outages","sales":"Plans and contracts"}
    cases=[
      ("negation_yes","The customer says they do not want a refund.","refund requested?"),
      ("double_negation","The customer says it is not impossible that they do not want a refund.","refund requested?"),
      ("contradiction_text","Customer: I want a refund. Metadata: refund=false.","refund requested?"),
      ("contradiction_meta","Customer: I do not want a refund. Metadata: refund=true.","refund requested?"),
      ("semantic_collision","The customer asks whether a duplicate card payment can be reversed, not about a technical outage.","Which department?"),
      ("ambiguous","The customer says something went wrong with a recent charge and asks for help.","Which department?"),
      ("sarcasm","Great, another mysterious charge. Exactly what I needed today.","Which department?"),
      ("turkish_negation","Müşteri iade istemediğini açıkça söylüyor.","İade talebi var mı?"),
      ("long_context","Background: "+("The customer mentions an old unrelated issue. "*180)+"Final: the customer was charged twice and wants a refund.","Which department?"),
    ]
    for name,state,instruction in cases:
        rows.append(run(judge,state,question(list(base.items()),instruction),{"experiment":"failure_surface","case":name}))
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default="results/behavioral-research-probes.json"); ap.add_argument("--only",default="all")
    a=ap.parse_args(); stamp=time.strftime("%Y%m%d-%H%M%S")
    j=HttpJudge("https://api.typesafe.ai",os.environ.get("TYPESAFE_API_KEY",""),"jev-1.13.0",cache_dir=ROOT/"json_cache"/f"behavior-{stamp}",max_retries=2)
    out={"created_at":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"model":"jev-1.13.0","experiments":{}}
    if a.only in ("all","candidate"): out["experiments"]["candidate_reduction"] = candidate_probes(j)
    if a.only in ("all","failure"): out["experiments"]["failure_surface"] = failure_probes(j)
    p=ROOT/a.out; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(p)
    for k,v in out["experiments"].items(): print(k,len(v),"rows",sum(1 for x in v if x.get("ok")))
if __name__=="__main__": main()
