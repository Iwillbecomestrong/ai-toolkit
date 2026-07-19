#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys

REQUIRED_SKILLS = {
 'patch-using-superpowers','patch-brainstorming','patch-writing-plans','patch-challenging-plans',
 'patch-parallel-dag-development','patch-dag-worktree-development','patch-subagent-driven-development','patch-sol-final-audit'
}
REQUIRED_AGENTS = {'patch-investigator.md','patch-plan-challenger.md','patch-tdd-implementer.md','patch-integration-operator.md'}

def fm_name(path: Path) -> str:
    text=path.read_text(encoding='utf-8')
    m=re.search(r'^name:\s*([^\n]+)$', text, re.M)
    return m.group(1).strip() if m else ''

def verify(root: Path) -> list[str]:
    errors=[]
    manifest_path=root/'.claude-plugin/plugin.json'
    if not manifest_path.exists(): return ['缺少 .claude-plugin/plugin.json']
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('name')!='patch-superpowers': errors.append('plugin name 错误')
    if manifest.get('version')!='2.4.0': errors.append('plugin version 错误')
    if (root/'hooks').exists(): errors.append('v2.4.0 不应包含 hooks')
    skills={p.name for p in (root/'skills').iterdir() if p.is_dir()}
    if skills!=REQUIRED_SKILLS: errors.append(f'Skill 集合不符: {sorted(skills)}')
    for name in skills:
        p=root/'skills'/name/'SKILL.md'
        if not p.exists(): errors.append(f'{name} 缺少 SKILL.md')
        elif fm_name(p)!=name: errors.append(f'{name} frontmatter name 不一致')
    agents={p.name for p in (root/'agents').glob('*.md')}
    if agents!=REQUIRED_AGENTS: errors.append(f'Agent 集合不符: {sorted(agents)}')
    config=json.loads((root/'config/model-routing.json').read_text(encoding='utf-8'))
    roles=config.get('codex_cli_roles',{})
    for role in ['core_planner','detailed_planner','repair_planner','plan_patch','final_auditor']:
        if roles.get(role,{}).get('model')!='gpt-5.6-sol': errors.append(f'{role} model 错误')
    for role in ['task_reviewer','integration_reviewer']:
        if roles.get(role,{}).get('model')!='gpt-5.6-luna': errors.append(f'{role} model 错误')
    scan_roots=[root/'skills', root/'agents', root/'config', root/'bin', root/'docs']
    all_text='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for base in scan_roots if base.exists() for p in base.rglob('*') if p.is_file() and p.suffix in {'.md','.json','.py'})
    for token in ['task-wave-development','cluster-worktree-development','superpowers-wave-integration-operator']:
        if token in all_text: errors.append(f'发现旧资产引用: {token}')
    for token in ['MUST_FOLLOW','CONFIRMED_FACTS','UNKNOWN','REFERENCE_ONLY_PATHS','REFERENCE_ACCESS_REQUIRED','UNVERIFIED_REFERENCE']:
        if token not in all_text: errors.append(f'缺少语义: {token}')
    return errors

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--source',type=Path,default=Path(__file__).resolve().parent); a=ap.parse_args()
    errors=verify(a.source.resolve())
    if errors:
        print('VERIFY_FAILED'); [print('- '+e) for e in errors]; return 1
    print('VERIFY_OK'); print('PLUGIN=patch-superpowers'); print('VERSION=2.4.0'); print('HOOKS=NONE'); print('REFERENCE_ACCESS=DEFERRED'); return 0
if __name__=='__main__': raise SystemExit(main())
