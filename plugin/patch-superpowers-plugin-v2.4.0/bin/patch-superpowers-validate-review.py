#!/usr/bin/env python3
"""校验 Task/Integration/Final Review 的关键证据字段。"""
from __future__ import annotations
import argparse,re
from pathlib import Path

RULES={
 'task':(['TASK_ID','TASK_BASE_COMMIT','REVIEWED_HEAD_COMMIT','DIFF_SHA256','REVIEWER_THREAD_ID','STATUS:'], {'APPROVED','REQUEST_CHANGES','PLAN_PATCH_REQUIRED','BLOCKED_EVIDENCE'}),
 'task-rereview':(['TASK_ID','PREVIOUS_REVIEW_PATH','PREVIOUS_OPEN_FINDING_IDS','OPEN_FINDING_IDS','STATUS:'], {'APPROVED','REQUEST_CHANGES','PLAN_PATCH_REQUIRED','BLOCKED_EVIDENCE'}),
 'integration':(['GATE_ID','CANDIDATE_BASE_COMMIT','CANDIDATE_COMMIT','DIFF_SHA256','STATUS:'], {'PASSED','FAILED','PLAN_PATCH_REQUIRED','BLOCKED_EVIDENCE'}),
 'final':(['SPEC_PATH','PLAN_PATH','FINAL_COMMIT','FINAL_DIFF_SHA256','AUDITOR_THREAD_ID','STATUS:'], {'READY_FOR_USER_ACCEPTANCE','LOCAL_FIX_REQUIRED','COMPLEX_REPAIR_PLAN_REQUIRED','PLAN_PATCH_REQUIRED','BLOCKED_EVIDENCE'})
}

def validate(text:str,kind:str)->list[str]:
    required, verdicts=RULES[kind]; errors=[]
    for token in required:
        if token not in text: errors.append(f'缺少字段: {token}')
    m=re.search(r'STATUS:\s*`?([A-Z_]+)',text)
    if not m: errors.append('缺少可解析 STATUS')
    elif m.group(1) not in verdicts: errors.append(f'不允许的 STATUS: {m.group(1)}')
    if kind in {'task','task-rereview','integration','final'} and 'Finding' not in text and 'FINDING' not in text:
        errors.append('缺少 Finding 区域')
    return errors

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('file',type=Path); ap.add_argument('--kind',choices=RULES,required=True); a=ap.parse_args()
    errs=validate(a.file.read_text(encoding='utf-8'),a.kind)
    if errs:
        print('REVIEW_INVALID'); [print(f'- {e}') for e in errs]; return 1
    print('REVIEW_VALID'); return 0
if __name__=='__main__': raise SystemExit(main())
