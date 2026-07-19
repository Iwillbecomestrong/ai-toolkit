#!/usr/bin/env python3
"""动态 READY 计算、状态初始化和 protected-dev 准入锁。"""
from __future__ import annotations
import argparse, json, os, re, subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

class RuntimeErrorDAG(RuntimeError): pass
TASK_DONE={'IN_DEV'}
GATE_UPSTREAM_DONE={'APPROVED','ADMISSION_PENDING','IN_DEV'}
NOT_STARTED={'PLANNED','BLOCKED_DEPENDENCY','READY'}

def load(path:Path)->dict[str,Any]:
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict): raise RuntimeErrorDAG(f'JSON 根必须是对象: {path}')
    return data

def status(mapping:dict[str,Any], item_id:str)->str:
    return str(mapping.get(item_id,{}).get('status','PLANNED'))

def compute_ready_tasks(manifest:dict[str,Any], state:dict[str,Any])->list[str]:
    ts=state.get('tasks',{}); gs=state.get('gates',{}); ready=[]
    for t in manifest.get('tasks',[]):
        tid=str(t['id'])
        if status(ts,tid) not in NOT_STARTED: continue
        if not all(status(ts,str(d)) in TASK_DONE for d in t.get('depends_on',[])): continue
        if not all(status(gs,str(g))=='PASSED' for g in t.get('depends_on_gates',[])): continue
        ready.append((-int(t.get('weight',1)),tid))
    ready.sort(); return [tid for _,tid in ready]

def compute_ready_gates(manifest:dict[str,Any], state:dict[str,Any])->list[str]:
    ts=state.get('tasks',{}); gs=state.get('gates',{}); ready=[]
    for g in manifest.get('integration_gates',[]):
        gid=str(g['id'])
        if status(gs,gid) not in NOT_STARTED: continue
        ups=[str(x) for x in g.get('upstream_tasks',[])]
        if ups and all(status(ts,x) in GATE_UPSTREAM_DONE for x in ups): ready.append(gid)
    return sorted(ready)

def initial_state(manifest:dict[str,Any], epic_id:str='', dev_branch:str='dev', dev_commit:str='')->dict[str,Any]:
    return {
      'schema_version':5,'epic_id':epic_id or str(manifest.get('epic_id','')),
      'protected_dev_branch':dev_branch,'protected_dev_commit':dev_commit,'last_stable_dev_commit':dev_commit,
      'capacity':{'claude_work_pool':5,'luna_review_pool':5},
      'queues':{'ready_tasks':[],'ready_gates':[],'ready_for_review':[],'admission_queue':[],'repair_queue':[]},
      'active':{'claude_sessions':{},'luna_sessions':{}},
      'tasks':{str(t['id']):{'status':'PLANNED','attempts':0} for t in manifest.get('tasks',[])},
      'gates':{str(g['id']):{'status':'PLANNED','attempts':0} for g in manifest.get('integration_gates',[])},
      'admission_lock':{'status':'free','holder':'','acquired_at':''},'failure_registry':{},'repair_attempts':{}
    }

def refresh(manifest:dict[str,Any], state:dict[str,Any])->dict[str,Any]:
    state.setdefault('queues',{})['ready_tasks']=compute_ready_tasks(manifest,state)
    state['queues']['ready_gates']=compute_ready_gates(manifest,state)
    for tid,item in state.get('tasks',{}).items():
        if item.get('status') in NOT_STARTED:
            item['status']='READY' if tid in state['queues']['ready_tasks'] else 'BLOCKED_DEPENDENCY'
    for gid,item in state.get('gates',{}).items():
        if item.get('status') in NOT_STARTED:
            item['status']='READY' if gid in state['queues']['ready_gates'] else 'BLOCKED_DEPENDENCY'
    return state

def git(repo:Path,*args:str)->str:
    p=subprocess.run(['git',*args],cwd=repo,text=True,capture_output=True)
    if p.returncode: raise RuntimeErrorDAG(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()

def safe_id(v:str)->str:
    if not re.fullmatch(r'[A-Za-z0-9._-]+',v): raise RuntimeErrorDAG(f'不安全 id: {v}')
    return v

def prepare_task(repo:Path,task_id:str,base:str,root:Path)->dict[str,str]:
    task_id=safe_id(task_id); commit=git(repo,'rev-parse','--verify',f'{base}^{{commit}}'); branch=f'task/{task_id}'
    root.mkdir(parents=True,exist_ok=True); path=root/task_id
    if path.exists(): raise RuntimeErrorDAG(f'worktree 已存在: {path}')
    if git(repo,'branch','--list',branch): raise RuntimeErrorDAG(f'branch 已存在: {branch}')
    git(repo,'worktree','add','-b',branch,str(path),commit)
    return {'task_id':task_id,'branch':branch,'worktree':str(path),'base_commit':commit}

@contextmanager
def admission_lock(repo:Path)->Iterator[Path]:
    common=Path(git(repo,'rev-parse','--git-common-dir'))
    if not common.is_absolute(): common=(repo/common).resolve()
    lock=common/'parallel-superpowers-dev-admission.lock'
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError as exc: raise RuntimeErrorDAG(f'protected dev 准入已被占用: {lock}') from exc
    try:
        os.write(fd,f'pid={os.getpid()}\n'.encode()); os.close(fd); yield lock
    finally:
        try: lock.unlink()
        except FileNotFoundError: pass

def main()->int:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('init'); p.add_argument('--manifest',type=Path,required=True); p.add_argument('--state',type=Path,required=True); p.add_argument('--dev-branch',default='dev'); p.add_argument('--dev-commit',default='')
    p=sub.add_parser('ready'); p.add_argument('--manifest',type=Path,required=True); p.add_argument('--state',type=Path,required=True)
    p=sub.add_parser('prepare-task'); p.add_argument('--repo',type=Path,required=True); p.add_argument('--task',required=True); p.add_argument('--base',required=True); p.add_argument('--worktree-root',type=Path,required=True)
    a=ap.parse_args()
    try:
        if a.cmd=='init':
            m=load(a.manifest); s=refresh(m,initial_state(m,dev_branch=a.dev_branch,dev_commit=a.dev_commit)); a.state.parent.mkdir(parents=True,exist_ok=True); a.state.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(a.state); return 0
        if a.cmd=='ready':
            m,s=load(a.manifest),load(a.state); refresh(m,s); a.state.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'ready_tasks':s['queues']['ready_tasks'],'ready_gates':s['queues']['ready_gates']},ensure_ascii=False)); return 0
        if a.cmd=='prepare-task': print(json.dumps(prepare_task(a.repo,a.task,a.base,a.worktree_root),ensure_ascii=False)); return 0
    except (OSError,ValueError,RuntimeErrorDAG) as exc:
        print(f'ERROR: {exc}'); return 1
    return 2
if __name__=='__main__': raise SystemExit(main())
