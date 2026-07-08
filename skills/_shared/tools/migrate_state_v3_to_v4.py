#!/usr/bin/env python3
"""
migrate_state_v3_to_v4.py — V3 STATE.json → V4 STATE.json migration

将旧的单状态机 STATE.json (schema_version=3) 迁移到多 pipeline 7 状态 (schema_version=4).

Usage:
  python migrate_state_v3_to_v4.py <path_to_v3_state.json> [--dry-run] [--output <path>]
"""

import json, sys, os
from datetime import datetime

# Phase → Pipeline state mapping
PHASE_TO_PIPELINE_STATE = {
    "intake": "计划",
    "research": "计划",
    "planning": "计划",
    "plan_review": "计划",
    "development": "开发",
    "testing": "测试",
    "acceptance": "验收",
    "fixing": "开发",
    "integration": "测试",
    "verification": "验收",
    "done": "已完成",
    "blocked": "暂停",
}

# Phase → Category (best-effort)
PHASE_TO_CATEGORY = {
    "intake": "unknown",
    "research": "unknown",
    "planning": "unknown",
    "plan_review": "unknown",
    "development": "default",
    "testing": "default",
    "acceptance": "default",
    "fixing": "default",
    "integration": "default",
    "verification": "default",
    "done": "default",
    "blocked": "default",
}

def migrate_v3_to_v4(v3_state):
    old_phase = v3_state.get("current_phase", "intake")
    old_category = v3_state.get("current_category", "default") or "default"

    pipeline_id = f"pipeline-{old_category}"

    v4 = {
        "task_id": v3_state.get("task_id", f"migrated-{datetime.now().strftime('%Y%m%d-%H%M%S')}"),
        "schema_version": 4,
        "global_state": "active" if old_phase != "blocked" else "blocked",
        "blocked_reason": v3_state.get("block_reason") if old_phase == "blocked" else None,
        "pipelines": {
            pipeline_id: {
                "category": old_category,
                "state": PHASE_TO_PIPELINE_STATE.get(old_phase, "计划"),
                "previous_state": None,
                "plan_status": v3_state.get("plan_status", "pending"),
                "plan_file": v3_state.get("plan_file"),
                "reviewer_status": v3_state.get("plan_review_status", "pending"),
                "test_target_report": None,
                "last_commit": None,
                "branch": "",
                "worktree": None,
                "created_at": v3_state.get("created_at", datetime.now().isoformat()),
                "updated_at": v3_state.get("updated_at", datetime.now().isoformat()),
            }
        },
        "current_pipeline": pipeline_id,
        "verification_status": v3_state.get("verification_status", "pending"),
        "created_at": v3_state.get("created_at", datetime.now().isoformat()),
        "updated_at": datetime.now().isoformat(),
    }
    return v4

def main():
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if len(args) < 1:
        print(f"Usage: {sys.argv[0]} <v3_state.json> [--dry-run] [--output <path>]")
        sys.exit(1)

    input_path = args[0]
    with open(input_path, "r", encoding="utf-8") as f:
        v3 = json.load(f)

    v4 = migrate_v3_to_v4(v3)

    output_path = next((args[i+1] for i, a in enumerate(args) if a == "--output" and i+1 < len(args)), None)
    output = json.dumps(v4, indent=2, ensure_ascii=False)

    if dry_run:
        print("=== DRY RUN ===")
        print(f"Input:  {input_path}")
        print(f"Output: {output_path or '(stdout)'}")
        print()
        print(output)
        print()
        print("=== DRY RUN COMPLETE (no files written) ===")
    elif output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Migrated: {input_path} → {output_path}")
    else:
        print(output)

if __name__ == "__main__":
    main()
