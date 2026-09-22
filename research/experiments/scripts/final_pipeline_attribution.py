"""Final controlled experiment: global scoring vs cluster filtering vs order bias."""
from __future__ import annotations
import argparse, json, math, os, random, statistics, time, uuid
from collections import Counter
from pathlib import Path
from harness.judge.http import HttpJudge
from harness.judge.base import to_plain

ROOT=Path(__file__).resolve().parents[1]
class NoCacheJudge(HttpJudge):
    def _read_cache(self,key): return None
    def _write_cache(self,key,entry): return None
def entropy(p): return -sum(float(v)*math.log2(float(v)) for v in p.values() if float(v)>0)
def make_desc(cluster, i, target=False):
    if target: core="duplicate invoice charge refund"
    else:
        cores={"billing":"invoice payment support","refund":"refund return transaction","payment":"payment transaction processing","subscription":"subscription renewal plan","fraud":"fraud risk verification","account":"account profile management","support":"customer support request","technical":"technical system issue","security":"security access protection","legal":"legal policy compliance"}
        core=cores[cluster]
    # Fixed sentence structure and fixed word count for every candidate.
    return f"This candidate handles {core} cases and related operational requests. It is an option in the category." 
def build_clusters(target_pos, rng):
    names=["billing","refund","payment","subscription","fraud","account","support","technical","security","legal"]
    clusters={}
    for c in names:
        vals=[]
        for i in range(25):
            rid="opt_"+uuid.uuid4().hex[:10]
            vals.append({"id":rid,"cluster":c,"target":c=="billing" and i==target_pos-1,"desc":make_desc(c,i,c=="billing" and i==target_pos-1)})
        rng.shuffle(vals); clusters[c]=vals
        # restore exact controlled target index after randomizing non-target members
        if c=="billing":
            target=next(x for x in vals if x["target"]); others=[x for x in vals if not x["target"]]; rng.shuffle(others); vals=others[:target_pos-1]+[target]+others[target_pos-1:]; clusters[c]=vals
    return clusters
def ordered_options(clusters, layout, rng):
    names=list(clusters); target="billing"; others=[x for x in names if x!=target]; rng.shuffle(others)
    if layout=="first": order=[target]+others
    elif layout=="last": order=others+[target]
    elif layout=="middle": order=others[:4]+[target]+others[4:]
    else: order=names; rng.shuffle(order)
    if layout=="interleaved":
        out=[]
        for i in range(25):
            for c in order: out.append(clusters[c][i])
    else: out=[x for c in order for x in clusters[c]]
    return out, order
def call(j,state,opts,meta):
    t=time.perf_counter()
    try:
        r=j.system_one(state,{"route":{"type":"choice","instructions":"Which candidate best handles the described case?","criteria":{x["id"]:x["desc"] for x in opts}}})
        a=to_plain(r.answers)["route"]; p=a.get("probabilities",{}); target=next(x["id"] for x in opts if x["target"]); cluster={x["id"] for x in opts if x["cluster"]=="billing"}
        return {**meta,"ok":True,"ms":round((time.perf_counter()-t)*1000,2),"choice":a.get("choice"),"confidence":a.get("confidence"),"target_mass":float(p.get(target,0.0)),"cluster_mass":sum(float(p.get(k,0.0)) for k in cluster),"entropy_bits":round(entropy(p),6),"target_id":target,"target_index":next(i for i,x in enumerate(opts,1) if x["target"]),"choice_in_cluster":next((x["cluster"] for x in opts if x["id"]==a.get("choice")),None)}
    except Exception as e: return {**meta,"ok":False,"ms":round((time.perf_counter()-t)*1000,2),"error":f"{type(e).__name__}: {e}"}
def summarize(rows):
    good=[r for r in rows if r.get("ok")]
    if not good:return {"n":len(rows),"successful":0,"errors":dict(Counter(r.get("error","") for r in rows))}
    def stats(k):
        x=[float(r[k]) for r in good]; return {"mean":statistics.mean(x),"stdev":statistics.pstdev(x),"min":min(x),"max":max(x)}
    return {"n":len(rows),"successful":len(good),"latency_ms":stats("ms"),"target_mass":stats("target_mass"),"cluster_mass":stats("cluster_mass"),"confidence":stats("confidence"),"entropy_bits":stats("entropy_bits"),"winner_counts":dict(Counter(r.get("choice_in_cluster") for r in good)),"target_winner_count":sum(r.get("choice")==r.get("target_id") for r in good),"cluster_winner_count":sum(r.get("choice_in_cluster")=="billing" for r in good)}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repeats",type=int,default=30); ap.add_argument("--only",default="all"); ap.add_argument("--out",default="results/final-pipeline-attribution.json"); a=ap.parse_args()
    selected=set(("first,middle,last,interleaved" if a.only=="all" else a.only).split(",")); rng=random.Random(20260922)
    j=NoCacheJudge("https://api.typesafe.ai",os.environ.get("TYPESAFE_API_KEY",""),"jev-1.13.0",cache_dir=ROOT/"json_cache"/f"final-attrib-{time.strftime('%Y%m%d-%H%M%S')}",max_retries=0)
    raw=[]; summaries={}; state="The customer was charged twice for the same invoice and wants the duplicate payment refunded."
    for layout in selected:
        if layout not in {"first","middle","last","interleaved"}: continue
        for pos in (1,5,10,15,20,25):
            rows=[]
            for rep in range(a.repeats):
                clusters=build_clusters(pos,rng); opts,order=ordered_options(clusters,layout,rng)
                rows.append(call(j,state+f" [controlled layout={layout} target_position={pos} repeat={rep}]",opts,{"experiment":"final_pipeline","layout":layout,"target_position":pos,"repeat":rep,"option_count":len(opts),"cluster_order":order}))
            raw.extend(rows); summaries[f"{layout}:target_{pos}"]=summarize(rows); print(layout,pos,summaries[f"{layout}:target_{pos}"]["successful"],"/",a.repeats,flush=True)
    p=ROOT/a.out;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({"created_at":time.strftime('%Y-%m-%dT%H:%M:%S%z'),"repeats":a.repeats,"raw":raw,"summaries":summaries},ensure_ascii=False,indent=2),encoding="utf-8");print(p)
if __name__=="__main__":main()
