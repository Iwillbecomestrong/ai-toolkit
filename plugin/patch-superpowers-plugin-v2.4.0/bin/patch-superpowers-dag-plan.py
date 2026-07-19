#!/usr/bin/env python3
"""解析并验证 schema-5 Execution Task DAG manifest。"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from typing import Any

FENCE = re.compile(r"```execution-dag-manifest\s*(\{.*?\})\s*```", re.S | re.I)

class PlanError(ValueError): pass

def extract_manifest(text: str) -> dict[str, Any]:
    matches = FENCE.findall(text)
    if len(matches) != 1:
        raise PlanError(f"计划必须且只能包含一个 execution-dag-manifest，当前数量={len(matches)}")
    try: data = json.loads(matches[0])
    except json.JSONDecodeError as exc: raise PlanError(f"manifest JSON 无效: {exc}") from exc
    if not isinstance(data, dict): raise PlanError("manifest 根必须是对象")
    return data

def validate_manifest(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get('schema_version') != 5: errors.append('schema_version 必须为 5')
    tasks = data.get('tasks')
    gates = data.get('integration_gates')
    if not isinstance(tasks, list) or not tasks: errors.append('tasks 必须是非空数组'); tasks=[]
    if not isinstance(gates, list): errors.append('integration_gates 必须是数组'); gates=[]
    task_ids=[str(t.get('id','')).strip() for t in tasks if isinstance(t,dict)]
    gate_ids=[str(g.get('id','')).strip() for g in gates if isinstance(g,dict)]
    if any(not x for x in task_ids): errors.append('每个 Task 必须有 id')
    if len(task_ids)!=len(set(task_ids)): errors.append('Task id 重复')
    if any(not x for x in gate_ids): errors.append('每个 Gate 必须有 id')
    if len(gate_ids)!=len(set(gate_ids)): errors.append('Gate id 重复')
    task_set, gate_set=set(task_ids), set(gate_ids)
    graph={x:[] for x in task_ids}
    for t in tasks:
        if not isinstance(t,dict): errors.append('Task 必须是对象'); continue
        tid=str(t.get('id',''))
        deps=t.get('depends_on',[]); gdeps=t.get('depends_on_gates',[]); regions=t.get('write_regions',[])
        if not isinstance(deps,list): errors.append(f'{tid}: depends_on 必须是数组'); deps=[]
        if not isinstance(gdeps,list): errors.append(f'{tid}: depends_on_gates 必须是数组'); gdeps=[]
        if not isinstance(regions,list) or not regions: errors.append(f'{tid}: write_regions 必须是非空数组')
        for d in map(str,deps):
            if d not in task_set: errors.append(f'{tid}: 未知 Task 依赖 {d}')
            elif d==tid: errors.append(f'{tid}: 不能依赖自己')
            else: graph[d].append(tid)
        for g in map(str,gdeps):
            if g not in gate_set: errors.append(f'{tid}: 未知 Gate 依赖 {g}')
        try:
            if int(t.get('weight',1)) < 1: errors.append(f'{tid}: weight 必须 >= 1')
        except Exception: errors.append(f'{tid}: weight 必须是整数')
    for g in gates:
        if not isinstance(g,dict): errors.append('Gate 必须是对象'); continue
        gid=str(g.get('id','')); upstream=g.get('upstream_tasks',[])
        if not isinstance(upstream,list) or not upstream: errors.append(f'{gid}: upstream_tasks 必须是非空数组'); continue
        for t in map(str,upstream):
            if t not in task_set: errors.append(f'{gid}: 未知上游 Task {t}')
    indeg={x:0 for x in task_ids}
    for src, outs in graph.items():
        for dst in outs: indeg[dst]+=1
    queue=[x for x,d in indeg.items() if d==0]; seen=0
    while queue:
        n=queue.pop(); seen+=1
        for dst in graph[n]:
            indeg[dst]-=1
            if indeg[dst]==0: queue.append(dst)
    if seen != len(task_ids): errors.append('Task DAG 存在环')
    return errors

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('plan',type=Path); ap.add_argument('--output',type=Path)
    a=ap.parse_args()
    try:
        m=extract_manifest(a.plan.read_text(encoding='utf-8')); errs=validate_manifest(m)
    except (OSError,PlanError) as exc:
        print(f'PLAN_INVALID\n- {exc}'); return 1
    if errs:
        print('PLAN_INVALID'); [print(f'- {e}') for e in errs]; return 1
    out=a.output or a.plan.with_suffix(a.plan.suffix+'.dag.json')
    out.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PLAN_VALID'); print(out); return 0
if __name__=='__main__': raise SystemExit(main())
