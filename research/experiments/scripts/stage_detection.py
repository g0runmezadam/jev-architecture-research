"""Cache-free black-box probes for single-stage vs multi-stage Jev inference."""
from __future__ import annotations
import argparse, json, math, os, statistics, time
from pathlib import Path
from collections import Counter
from harness.judge.http import HttpJudge
from harness.judge.base import to_plain

ROOT=Path(__file__).resolve().parents[1]

class NoCacheJudge(HttpJudge):
    def _read_cache(self, key): return None
    def _write_cache(self, key, entry): return None

def entropy(p): return -sum(float(v)*math.log2(float(v)) for v in p.values() if float(v)>0)

def q(options):
    return {"type":"choice","instructions":"Which category best matches the request?",
            "criteria":{k:v for k,v in options}}

def base_options():
    return [("billing","Invoices, payments, charges and refunds"),
            ("technical","Bugs, outages and API errors"),
            ("sales","Plans, contracts and purchasing")]

def call(j,state,options,meta):
    t=time.perf_counter()
    try:
        r=j.system_one(state,{"route":q(options)})
        a=to_plain(r.answers)["route"]; p=a.get("probabilities",{})
        return {**meta,"ok":True,"ms":round((time.perf_counter()-t)*1000,2),
                "choice":a.get("choice"),"confidence":a.get("confidence"),
                "target_probability":p.get("billing"),"entropy_bits":round(entropy(p),6),
                "probabilities":p,"input_tokens":r.input_tokens}
    except Exception as e:
        return {**meta,"ok":False,"ms":round((time.perf_counter()-t)*1000,2),
                "error":f"{type(e).__name__}: {e}"}

def near_duplicate_options(n):
    return [("billing","Invoices, payments, charges and refunds")]+[(f"billing_variant_{i:03d}",f"A near-duplicate billing category covering invoices, payments, charges and refunds; wording variant {i}.") for i in range(n)]+[("technical","Bugs, outages and API errors")]

def adversarial_options(n):
    return [("billing","Invoices, payments, charges and refunds")]+[(f"billing_shadow_{i:03d}","A customer was charged twice for the same invoice and wants the duplicate payment refunded.") for i in range(n)]+[("technical","Bugs, outages and API errors")]

def scaling_options(n):
    return [("billing","Invoices, payments, charges and refunds")]+[(f"decoy_{i:04d}",f"Unrelated category {i}: general support topic") for i in range(n-1)]

def winner_variants():
    return [
      ("billing","Invoices, payments, charges and refunds"),
      ("billing","Duplicate invoice payment and refund request"),
      ("billing","The same payment was charged twice; customer wants money back"),
      ("billing","Billing issue involving an invoice and duplicate charge"),
      ("billing","Payment reversal for a repeated invoice charge"),
    ]

def summarize(rows):
    good=[x for x in rows if x.get("ok")]
    if not good: return {"n":len(rows),"successful":0,"errors":Counter(x.get("error","") for x in rows)}
    lat=[x["ms"] for x in good]; probs=[float(x["target_probability"] or 0) for x in good]
    conf=[float(x["confidence"] or 0) for x in good]; ent=[float(x["entropy_bits"]) for x in good]
    winners=Counter(x.get("choice") for x in good)
    return {"n":len(rows),"successful":len(good),"errors":dict(Counter(x.get("error","") for x in rows if not x.get("ok"))),
            "latency_ms":{"min":min(lat),"p50":statistics.median(lat),"p95":sorted(lat)[max(0,math.ceil(.95*len(lat))-1)],"max":max(lat)},
            "target_probability":{"mean":statistics.mean(probs),"stdev":statistics.pstdev(probs),"min":min(probs),"max":max(probs)},
            "confidence":{"mean":statistics.mean(conf),"stdev":statistics.pstdev(conf)},
            "entropy_bits":{"mean":statistics.mean(ent),"stdev":statistics.pstdev(ent)},"winner_counts":dict(winners)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repeats",type=int,default=30); ap.add_argument("--only",default="all"); ap.add_argument("--out",default="results/stage-detection.json"); a=ap.parse_args()
    stamp=time.strftime("%Y%m%d-%H%M%S")
    j=NoCacheJudge("https://api.typesafe.ai",os.environ.get("TYPESAFE_API_KEY",""),"jev-1.13.0",cache_dir=ROOT/"json_cache"/f"stage-{stamp}",max_retries=0,timeout=60)
    state="The customer was charged twice for the same invoice and wants the duplicate payment refunded."
    selected=set(("near,winner,adversarial,scaling" if a.only=="all" else a.only).split(","))
    conditions=[]
    if "near" in selected: conditions += [("near_duplicate_explosion",n,near_duplicate_options(n)) for n in (10,25,50,100,250)]
    if "winner" in selected: conditions += [("winner_variant",i,[(v[0],v[1]),("technical","Bugs, outages and API errors"),("sales","Plans, contracts and purchasing")]) for i,v in enumerate(winner_variants())]
    if "adversarial" in selected: conditions += [("adversarial_insertion",n,adversarial_options(n)) for n in (1,10,25,50,100)]
    if "scaling" in selected: conditions += [("option_count_scaling",n,scaling_options(n)) for n in (5,10,25,50,100,250,500,1000)]
    raw=[]; summaries={}
    for ci,(kind,value,opts) in enumerate(conditions):
        rows=[]
        for rep in range(a.repeats):
            # Unique state marker disables local/API request de-duplication while preserving task semantics.
            s=state+f" [research repetition {ci}-{rep}; ignore this marker]"
            row=call(j,s,opts,{"experiment":kind,"condition":value,"repeat":rep,"option_count":len(opts)})
            rows.append(row); raw.append(row)
        summaries[f"{kind}:{value}"]=summarize(rows)
        print(kind,value,"ok",summaries[f"{kind}:{value}"].get("successful"),"/",a.repeats,flush=True)
    p=ROOT/a.out; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps({"created_at":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"repeats":a.repeats,"raw":raw,"summaries":summaries},ensure_ascii=False,indent=2),encoding="utf-8"); print(p)
if __name__=="__main__": main()
