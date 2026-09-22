"""Black-box reconstruction of Jev's semantic decision geometry."""
from __future__ import annotations
import argparse, json, math, os, time
from pathlib import Path
from harness.judge.http import HttpJudge
from harness.judge.base import to_plain

ROOT = Path(__file__).resolve().parents[1]

def entropy(p):
    return -sum(float(v)*math.log2(float(v)) for v in p.values() if float(v)>0)

def q(options, text="Which category best matches the request?"):
    return {"type":"choice", "instructions":text,
            "criteria": {name: desc for name, desc in options}}

def call(judge, state, question, meta):
    t=time.perf_counter()
    try:
        r=judge.system_one(state, {"route":question})
        a=to_plain(r.answers)["route"]
        p=a.get("probabilities", {})
        return {**meta, "ok":True, "ms":round((time.perf_counter()-t)*1000,2),
                "choice":a.get("choice"), "confidence":a.get("confidence"),
                "probabilities":p, "entropy_bits":round(entropy(p),6),
                "cached":r.cached, "input_tokens":r.input_tokens}
    except Exception as e:
        return {**meta, "ok":False, "ms":round((time.perf_counter()-t)*1000,2),
                "error":f"{type(e).__name__}: {e}"}

BASE=[("billing","Invoices, payments, charges and refunds"),
      ("technical","Bugs, outages, API errors and system failures"),
      ("sales","Plans, contracts and purchasing")]

def neighborhood(j):
    state="The customer was charged twice for the same invoice and wants the duplicate payment refunded."
    replacements=[
      ("unrelated","Plans, contracts and purchasing"),
      ("support_request","General customer support and help requests"),
      ("account_issue","Account profile and account-management problems"),
      ("subscription","Subscriptions, renewals and recurring plans"),
      ("refund","Requests to return money from a transaction"),
      ("duplicate_charge","A payment was charged twice or duplicated"),
      ("payment_issue","Incorrect, failed or duplicated payments"),
      ("invoice","Invoices, billing documents and invoice questions"),
    ]
    rows=[]
    for name,desc in replacements:
        opts=[("billing",BASE[0][1]),(name,desc),("technical",BASE[1][1])]
        rows.append(call(j,state+f" [neighborhood={name}]",q(opts),{"experiment":"neighborhood","replacement":name}))
    return rows

def distance_sweep(j):
    chain=[("billing","Invoices, payments, charges and refunds"),
           ("invoice","Invoices and billing documents"),
           ("payment_issue","Incorrect or duplicated payment"),
           ("account_issue","Account management issue"),
           ("support_request","General support request"),
           ("technical_issue","Technical bug, outage or API error")]
    state="The customer was charged twice for an invoice and wants the duplicate payment refunded."
    rows=[]
    for i,(name,desc) in enumerate(chain[1:],1):
        opts=[("billing",chain[0][1]),(name,desc)]
        rows.append(call(j,state+f" [distance_step={i}]",q(opts),{"experiment":"distance_sweep","step":i,"alternative":name}))
    return rows

def boundary(j):
    variants=[
      ("50_50","The customer reports a payment problem, but the message gives equal evidence for an invoice issue and a system failure."),
      ("60_40_billing","The customer mainly discusses an invoice and duplicate charge, with a small mention of a system error."),
      ("70_30_billing","The customer clearly focuses on a duplicate invoice charge; only a minor technical symptom is mentioned."),
      ("80_20_billing","The customer explicitly requests a refund for a duplicate payment; the technical detail is incidental."),
      ("60_40_technical","The customer mainly reports an API outage that caused a payment display error; billing is secondary."),
      ("70_30_technical","The customer clearly focuses on a login/API failure; the charge mention is incidental."),
      ("80_20_technical","The customer explicitly reports a system outage; the payment context is only background."),
    ]
    rows=[]
    opts=[("billing",BASE[0][1]),("technical",BASE[1][1])]
    for label,state in variants:
        rows.append(call(j,state+f" [boundary={label}]",q(opts,"Which issue is primary?"),{"experiment":"boundary","variant":label}))
    return rows

def entropy_surface(j):
    variants=[
      ("clear","The customer was charged twice and explicitly requests a refund for the duplicate invoice."),
      ("mild","The customer mentions a duplicate charge and asks for help, but does not clearly state whether a refund is wanted."),
      ("moderate","The customer says something went wrong with a recent charge; it might be an invoice problem or a technical display problem."),
      ("severe","The customer says only that there is an issue and asks us to determine whether it is billing or technical."),
    ]
    rows=[]; opts=[("billing",BASE[0][1]),("technical",BASE[1][1])]
    for label,state in variants:
        rows.append(call(j,state+f" [ambiguity={label}]",q(opts,"Which issue is best supported?"),{"experiment":"entropy_surface","ambiguity":label}))
    return rows

def competition(j):
    state="The customer was charged twice for the same invoice and wants the duplicate payment refunded."
    related=[("invoice","Invoices and billing documents"),("payment_issue","Incorrect or duplicated payment"),
             ("duplicate_charge","A payment was charged twice"),("refund","Requests to return transaction money"),
             ("subscription","Recurring subscriptions and renewals"),("account_issue","Account management problem"),
             ("support_request","General customer support request"),("technical_issue","Technical outage or bug")]
    rows=[]
    for n in (1,2,3,4,6,8):
        opts=[("billing",BASE[0][1])]+related[:n]+[("sales","Plans and contracts")]
        rows.append(call(j,state+f" [competition_n={n}]",q(opts),{"experiment":"semantic_competition","related_count":n,"option_count":len(opts)}))
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default="results/semantic-decision-geometry.json"); ap.add_argument("--only",default="all"); a=ap.parse_args()
    stamp=time.strftime("%Y%m%d-%H%M%S")
    j=HttpJudge("https://api.typesafe.ai",os.environ.get("TYPESAFE_API_KEY",""),"jev-1.13.0",cache_dir=ROOT/"json_cache"/f"geometry-{stamp}",max_retries=2)
    out={"created_at":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"model":"jev-1.13.0","experiments":{}}
    funcs={"neighborhood":neighborhood,"distance":distance_sweep,"boundary":boundary,"entropy":entropy_surface,"competition":competition}
    selected=set(funcs) if a.only=="all" else set(a.only.split(","))
    for name,fn in funcs.items():
        if name in selected:
            out["experiments"][name]=fn(j); print(name,len(out["experiments"][name]),sum(x.get("ok",False) for x in out["experiments"][name]),flush=True)
    p=ROOT/a.out; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8"); print(p)
if __name__=="__main__": main()
