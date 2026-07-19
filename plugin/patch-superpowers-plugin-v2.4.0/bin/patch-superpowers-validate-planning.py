#!/usr/bin/env python3
"""验证 Patch Superpowers 两阶段规划、输入分类和延迟参考门禁。"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any


def validate_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if state.get("schema_version") != 2:
        errors.append("planning state schema_version 必须为 2")

    must_follow = state.get("must_follow_files") or []
    unread = [str(x.get("id", "UNKNOWN")) for x in must_follow if x.get("status") != "READ_AND_APPLIED"]
    if unread:
        errors.append("MUST_FOLLOW 文件尚未完整读取并应用: " + ", ".join(unread))

    refs = state.get("reference_only_paths") or []
    for ref in refs:
        if ref.get("read_status") == "READ":
            if ref.get("access_status") != "APPROVED":
                errors.append(f"参考路径 {ref.get('id','UNKNOWN')} 未经 REFERENCE_ACCESS_REQUIRED 批准即被读取")
            if (state.get("solution_derivation") or {}).get("status") != "REFERENCE_ACCESS_REQUIRED":
                errors.append(f"参考路径 {ref.get('id','UNKNOWN')} 在独立调查仍可推导方案时被提前读取")

    claims = state.get("reference_claims") or []
    for claim in claims:
        if claim.get("used_in_plan") is True and claim.get("status") != "CONFIRMED":
            errors.append(f"UNVERIFIED_REFERENCE 不得进入计划: {claim.get('id','UNKNOWN')}")

    assumptions = state.get("assumptions") or []
    unresolved = [str(x.get("id","UNKNOWN")) for x in assumptions if x.get("type") == "LOAD_BEARING" and x.get("status") in {"UNKNOWN","INCONCLUSIVE",""}]
    if unresolved:
        errors.append("存在未关闭承重假设: " + ", ".join(unresolved))

    authority_changes = state.get("authority_changes") or []
    pending = [str(x.get("fact_id","UNKNOWN")) for x in authority_changes if x.get("change") is True and x.get("user_approval") != "APPROVED"]
    if pending:
        errors.append("权威判断修改尚未获得用户明确批准: " + ", ".join(pending))

    core = state.get("core_plan") or {}
    detailed = state.get("detailed_plan") or {}
    covered = set(core.get("must_follow_coverage") or [])
    required = {str(x.get("id")) for x in must_follow if x.get("id")}
    missing_coverage = sorted(required - covered)
    if missing_coverage:
        errors.append("CORE_PLAN 未覆盖 MUST_FOLLOW: " + ", ".join(missing_coverage))

    if core.get("user_approval") == "APPROVED" and not core.get("approval_id"):
        errors.append("核心计划已批准但缺少 approval_id")

    detailed_active = detailed.get("status") in {"DRAFT","READY","APPROVED"}
    if detailed_active:
        if core.get("challenge_status") != "PASS": errors.append("详细计划开始前核心计划必须通过 Claude 对抗审查")
        if core.get("user_approval") != "APPROVED": errors.append("详细计划开始前核心计划必须获得用户明确批准")
        if not core.get("approval_id"): errors.append("详细计划开始前必须记录核心计划 approval_id")
        if unresolved: errors.append("详细计划不能在承重假设未关闭时开始")
        if pending: errors.append("详细计划不能在权威判断修改未批准时开始")

    if detailed.get("status") in {"READY","APPROVED"} and detailed.get("challenge_status") != "PASS":
        errors.append("详细计划进入 READY/APPROVED 前必须通过一致性审查")

    if state.get("status") in {"DAG_EXECUTION","FINAL_VERIFICATION","FINAL_AUDIT","USER_ACCEPTANCE","DONE"} or detailed.get("status") == "APPROVED":
        if detailed.get("challenge_status") != "PASS": errors.append("进入执行前详细计划必须通过一致性审查")
        if detailed.get("user_approval") != "APPROVED": errors.append("进入执行前详细计划必须获得用户明确批准")
        if not detailed.get("approval_id"): errors.append("进入执行前详细计划必须记录 approval_id")
    return errors


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('state',type=Path); a=ap.parse_args()
    errors=validate_state(json.loads(a.state.read_text(encoding='utf-8')))
    if errors:
        print('PLANNING_VERIFY_FAILED'); [print('- '+e) for e in errors]; return 1
    print('PLANNING_VERIFY_OK'); return 0
if __name__=='__main__': raise SystemExit(main())
