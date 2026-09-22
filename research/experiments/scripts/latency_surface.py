"""Bounded latency surface map for questions/options/state size."""
from __future__ import annotations
import argparse, json, os, statistics, time
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

def run_one(judge,q,n,state_tokens):
    labels={f'o{i}':'x' for i in range(n)}
    questions={f'q{i}':{'type':'choice','instructions':'Which option is correct?','criteria':labels} for i in range(q)}
    state=' '.join(['context']*state_tokens)+f' target option o0 q{q} n{n}'
    t=time.perf_counter()
    try:
        r=judge.system_one(state,questions); answers=r.answers if isinstance(r.answers,dict) and all(isinstance(v,dict) for v in r.answers.values()) else to_plain(r.answers)
        return {'questions':q,'options':n,'state_tokens_requested':state_tokens,'answers':len(answers),'ms':(time.perf_counter()-t)*1000,'input_tokens':r.input_tokens,'output_tokens':r.output_tokens,'error':None}
    except Exception as e:
        return {'questions':q,'options':n,'state_tokens_requested':state_tokens,'answers':0,'ms':(time.perf_counter()-t)*1000,'input_tokens':0,'output_tokens':0,'error':f'{type(e).__name__}: {e}'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--out',default='results/latency-surface.json'); a=p.parse_args(); stamp=time.strftime('%Y%m%d-%H%M%S')
    judges={'laya-multilingual':LocalLaya(),'jev-1.13.0':HttpJudge('https://api.typesafe.ai',os.environ.get('TYPESAFE_API_KEY',''),'jev-1.13.0',cache_dir=ROOT/'json_cache'/f'latency-jev-{stamp}')}
    out={'created_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'grid':{'questions':[1,10,50,100],'options':[3,50,255],'state_tokens':[100,500,1000]},'results':{}}
    for name,j in judges.items():
        print('running',name,flush=True); rows=[]
        for st in out['grid']['state_tokens']:
            for n in out['grid']['options']:
                for q in out['grid']['questions']:
                    row=run_one(j,q,n,st); rows.append(row); print(name,st,n,q,row['ms'],row['error'] or '',flush=True)
        out['results'][name]=rows
    path=ROOT/a.out; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print('saved',path)
if __name__=='__main__': main()
