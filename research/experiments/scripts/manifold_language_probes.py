"""Semantic manifold, information bottleneck, confidence attack and language probes."""
from __future__ import annotations
import argparse, json, os, time
from pathlib import Path
from types import SimpleNamespace
from harness.judge.base import to_plain
from harness.judge.http import HttpJudge
ROOT=Path(__file__).resolve().parents[1]

class LocalLaya:
    def __init__(self):
        import laya
        self.agent=laya.load('convaiinnovations/laya',subfolder='multilingual'); self.model='laya-multilingual'
    def system_one(self,state,questions):
        r=self.agent.predict(state,questions); return SimpleNamespace(model=self.model,answers=r['answers'],cached=False,input_tokens=r.get('usage',{}).get('input_tokens',0),output_tokens=0)

def ask(j,state,q):
    t=time.perf_counter(); r=j.system_one(state,q); a=r.answers if isinstance(r.answers,dict) and all(isinstance(v,dict) for v in r.answers.values()) else to_plain(r.answers)
    return {'answers':a,'ms':(time.perf_counter()-t)*1000,'input_tokens':r.input_tokens,'model':r.model}

CONCEPTS=['billing','invoice','payment_issue','duplicate_charge','refund','subscription','technical','bug','outage','account']
CONCEPT_DESC={
 'billing':'payments, refunds and charges','invoice':'billing documents and invoices','payment_issue':'failed or problematic payment transaction','duplicate_charge':'charged twice for the same purchase','refund':'returning money to the customer','subscription':'plans, renewal and cancellation','technical':'system or API technical problem','bug':'software defect or incorrect behavior','outage':'service unavailable or down','account':'login, profile and account settings'}

def manifold(j):
    rows=[]
    criteria={k:CONCEPT_DESC[k] for k in CONCEPTS}
    for source in CONCEPTS:
        r=ask(j,{'concept':source,'text':f'This ticket is about {source}.'},{'concept':{'type':'choice','instructions':'Which concept best matches the ticket?','criteria':criteria}})
        a=r['answers']['concept']; rows.append({'source':source,'choice':a.get('choice'),'confidence':a.get('confidence'),'probabilities':a.get('probabilities',{}),'ms':r['ms']})
    return rows

def information(j):
    states=[
        'The customer asks for help.',
        'The customer asks for help with an invoice.',
        'The customer says they were charged twice.',
        'The customer says the same card was charged twice.',
        'The customer says the same card was charged twice and explicitly requests a refund.'
    ]
    q={'route':{'type':'choice','instructions':'Which department should handle this?','criteria':{'billing':'payments, invoices and refunds','technical':'bugs and outages','sales':'plans and contracts','account':'login and profile'}}}
    return [{'step':i+1,'state':s,'answer':(r:=ask(j,s,q))['answers']['route'],'ms':r['ms']} for i,s in enumerate(states)]

def counterfactual(j):
    phrases=['refund requested','refund not requested','refund maybe requested','refund probably requested','refund definitely requested']
    q={'refund':{'type':'noul','instructions':'Is the customer requesting a refund?'}}
    return [{'phrase':p,'answer':(r:=ask(j,{'message':f'The message says: {p}.'},q))['answers']['refund'],'ms':r['ms']} for p in phrases]

def confidence_attack(j):
    cases=[
      ('clear_billing',{'customer':'I was charged twice and want a refund.','metadata':{}},'billing'),
      ('clear_technical',{'customer':'The API returns 500 errors.','metadata':{}},'technical'),
      ('contradiction_billing',{'customer':'I want a refund.','metadata':{'department':'technical'}},'billing'),
      ('contradiction_technical',{'customer':'The API is broken.','metadata':{'department':'billing'}},'technical'),
      ('misleading_keyword',{'customer':'This is not a billing issue; the website is down.','metadata':{}},'technical'),
      ('negation',{'customer':'I do not want a refund; the charge is correct.','metadata':{}},'technical'),
      ('ambiguous','The charge looks strange and I am not sure what happened.','billing'),
      ('sarcasm','Great, another wonderful charge I absolutely wanted twice.','billing'),
      ('mixed',{'customer':'Refund requested but no payment was made.','metadata':{}},'billing'),
    ]
    q={'route':{'type':'choice','instructions':'Which department should handle this?','criteria':{'billing':'payments, invoices and refunds','technical':'bugs and outages','sales':'plans and contracts','account':'login and profile'}}}
    rows=[]
    for name,state,gold in cases:
        r=ask(j,state,q); a=r['answers']['route']; rows.append({'case':name,'gold':gold,'choice':a.get('choice'),'correct':a.get('choice')==gold,'confidence':a.get('confidence'),'probabilities':a.get('probabilities',{}),'ms':r['ms']})
    return rows

def language(j):
    states={
      'en':'I was charged twice for the same payment and want a refund.',
      'tr':'Aynı ödeme için iki kez ücretlendirildim ve para iadesi istiyorum.',
      'de':'Ich wurde für dieselbe Zahlung zweimal belastet und möchte eine Rückerstattung.',
      'fr':'J’ai été débité deux fois pour le même paiement et je souhaite un remboursement.',
      'es':'Me cobraron dos veces por el mismo pago y quiero un reembolso.',
      'ar':'تم تحميلي الرسوم مرتين لنفس الدفعة وأريد استرداد المبلغ.'}
    q={'route':{'type':'choice','instructions':'Which department should handle this request?','criteria':{'billing':'payments, invoices and refunds','technical':'bugs and outages','sales':'plans and contracts','account':'login and profile'}}}
    out=[]
    for lang,state in states.items():
        r=ask(j,state,q); a=r['answers']['route']; out.append({'language':lang,'choice':a.get('choice'),'confidence':a.get('confidence'),'probabilities':a.get('probabilities',{}),'ms':r['ms']})
    return out

def main():
    p=argparse.ArgumentParser(); p.add_argument('--out',default='results/manifold-language-probes.json'); a=p.parse_args(); stamp=time.strftime('%Y%m%d-%H%M%S')
    judges={'laya-multilingual':LocalLaya(),'jev-1.13.0':HttpJudge('https://api.typesafe.ai',os.environ.get('TYPESAFE_API_KEY',''),'jev-1.13.0',cache_dir=ROOT/'json_cache'/f'manifold-jev-{stamp}')}
    out={'created_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'concepts':CONCEPTS,'experiments':{}}
    for name,j in judges.items():
        print('running',name,flush=True); out['experiments'][name]={'manifold':manifold(j),'information_bottleneck':information(j),'counterfactual_geometry':counterfactual(j),'confidence_attack':confidence_attack(j),'language_invariance':language(j)}
    # Behavioral symmetric affinity graph from routing distributions.
    for name,data in out['experiments'].items():
        probs={row['source']:row['probabilities'] for row in data['manifold']}
        graph={}
        for a0 in CONCEPTS:
            graph[a0]={b0:round((float(probs.get(a0,{}).get(b0,0))+float(probs.get(b0,{}).get(a0,0)))/2,6) for b0 in CONCEPTS if b0!=a0}
        data['semantic_affinity_graph']=graph
    path=ROOT/a.out; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print('saved',path)
if __name__=='__main__': main()
