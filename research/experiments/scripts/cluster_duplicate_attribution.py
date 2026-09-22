"""Cluster-first and duplicate-competition probes for Jev attribution."""
from __future__ import annotations
import argparse, json, math, os, statistics, time
from collections import Counter
from pathlib import Path
from harness.judge.http import HttpJudge
from harness.judge.base import to_plain

ROOT=Path(__file__).resolve().parents[1]
class NoCacheJudge(HttpJudge):
    def _read_cache(self,key): return None
    def _write_cache(self,key,entry): return None
def entropy(p): return -sum(float(v)*math.log2(float(v)) for v in p.values() if float(v)>0)
def q(opts): return {"type":"choice","instructions":"Which category best matches the request?","criteria":dict(opts)}
def call(j,state,opts,meta):
    t=time.perf_counter()
    try:
        r=j.system_one(state,{"route":q(opts)}); a=to_plain(r.answers)["route"]; p=a.get("probabilities",{})
        return {**meta,"ok":True,"ms":round((time.perf_counter()-t)*1000,2),"choice":a.get("choice"),"confidence":a.get("confidence"),"entropy_bits":round(entropy(p),6),"target_probability":p.get("billing_000"),"cluster_probability":round(sum(float(v) for k,v in p.items() if k.startswith("billing_")),6),"probabilities":p}
    except Exception as e: return {**meta,"ok":False,"ms":round((time.perf_counter()-t)*1000,2),"error":f"{type(e).__name__}: {e}"}
def clusters():
    defs={"billing":"Invoices, payments, charges and refunds","technical":"Bugs, outages and API errors","sales":"Plans, contracts and purchasing","account":"Account profile and account management","security":"Security, fraud and unauthorized access","shipping":"Shipping, delivery and logistics","legal":"Legal, policy and compliance matters","product":"Product features and usage questions","support":"General customer support requests","identity":"Identity, login and authentication"}
    return {c:[(f"{c}_{i:03d}",f"{d}; cluster option wording variant {i}") for i in range(25)] for c,d in defs.items()}
def cluster_phase(j,repeats):
    cs=clusters(); state="The customer was charged twice for the same invoice and wants the duplicate payment refunded."
    names=list(cs); others=[c for c in names if c!="billing"]; orders={"first":["billing"]+others,"middle":others[:5]+["billing"]+others[5:],"last":others+["billing"]}
    orders["interleaved"]=[c for i in range(25) for c in names]; rows=[]
    for label,order in orders.items():
        opts=[x for c in order for x in cs[c]]
        for rep in range(repeats): rows.append(call(j,state+f" [cluster {label} repeat {rep}]",opts,{"experiment":"cluster_first","layout":label,"repeat":rep,"option_count":len(opts)}))
    return rows
def duplicate_phase(j,repeats):
    state="The customer was charged twice for the same invoice and wants the duplicate payment refunded."
    groups={"exact":[("billing_000","Invoices, payments, charges and refunds")]+[(f"dup_exact_{i:03d}","Invoices, payments, charges and refunds") for i in range(1,11)],"paraphrase":[("billing_000","Invoices, payments, charges and refunds")]+[(f"dup_para_{i:03d}",s) for i,s in enumerate(["Duplicate invoice payment needing a refund","Repeated charge on the same bill","Refund for two charges on one invoice","Customer was charged twice for a payment","Billing reversal for duplicate transaction","Payment duplicated and should be returned","Two identical invoice charges require refund","Repeated billing transaction","Double payment problem","Same invoice paid two times"],1)],"semantic":[("billing_000","Invoices, payments, charges and refunds")]+[(f"dup_sem_{i:03d}",s) for i,s in enumerate(["Payment problem","Refund request","Duplicate charge","Invoice issue","Transaction reversal","Billing support","Card charged twice","Money returned","Account payment issue","Charge dispute"],1)]}
    rows=[]
    for label,opts in groups.items():
        for rep in range(repeats): rows.append(call(j,state+f" [duplicate {label} repeat {rep}]",opts,{"experiment":"duplicate_competition","duplicate_type":label,"repeat":rep,"option_count":len(opts)}))
    return rows
def summarize(rows):
    good=[r for r in rows if r.get("ok")]
    if not good:return {"n":len(rows),"successful":0,"errors":dict(Counter(r.get("error","") for r in rows))}
    def stats(key):
        x=[float(r[key]) for r in good]; return {"mean":statistics.mean(x),"stdev":statistics.pstdev(x),"min":min(x),"max":max(x)}
    return {"n":len(rows),"successful":len(good),"latency_ms":stats("ms"),"confidence":stats("confidence"),"entropy_bits":stats("entropy_bits"),"target_probability":stats("target_probability"),"cluster_probability":stats("cluster_probability"),"winners":dict(Counter(r.get("choice") for r in good))}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repeats",type=int,default=30); ap.add_argument("--cluster-repeats",type=int,default=10); ap.add_argument("--only",default="all"); ap.add_argument("--out",default="results/cluster-duplicate-attribution.json"); a=ap.parse_args()
    stamp=time.strftime("%Y%m%d-%H%M%S"); j=NoCacheJudge("https://api.typesafe.ai",os.environ.get("TYPESAFE_API_KEY",""),"jev-1.13.0",cache_dir=ROOT/"json_cache"/f"attrib-{stamp}",max_retries=0)
    raw=[]; summaries={}
    if a.only in ("all","cluster"):
        rows=cluster_phase(j,a.cluster_repeats); raw+=rows
        for k in ("first","middle","last","interleaved"): summaries[f"cluster:{k}"]=summarize([r for r in rows if r["layout"]==k])
        print("cluster",len(rows),flush=True)
    if a.only in ("all","duplicate"):
        rows=duplicate_phase(j,a.repeats); raw+=rows
        for k in ("exact","paraphrase","semantic"): summaries[f"duplicate:{k}"]=summarize([r for r in rows if r["duplicate_type"]==k])
        print("duplicate",len(rows),flush=True)
    p=ROOT/a.out; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps({"created_at":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"raw":raw,"summaries":summaries},ensure_ascii=False,indent=2),encoding="utf-8"); print(p)
if __name__=="__main__": main()
