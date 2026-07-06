#!/usr/bin/env python3
"""
auto_dev_guard.py — PreToolUse / PostToolUse / Stop guard for auto-dev & multi-agent-core

Called by Claude Code hooks system. Reads tool invocation JSON from stdin,
checks against .ai-work/STATE.json (or .collab-work/STATE.json), and outputs
{ "decision": "allow" | "deny", "reason": "..." }.

Usage:
  python auto_dev_guard.py <hook_type> <state_dir>
  where hook_type = pretooluse | posttooluse | stop | userpromptsubmit

Input (stdin): JSON object from Claude Code hook system
Output (stdout): { "decision": "allow" | "deny", "reason": "...", "hook_type": "..." }
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime


# ── phase enum ──────────────────────────────────────────────────
VALID_PHASES = {
    "intake", "research", "planning", "plan_review",
    "development", "testing", "acceptance", "fixing",
    "integration", "verification", "done", "blocked"
}

# ── source directories (paths that trigger edit gate) ───────────
SOURCE_DIRS = ["app/", "src/", "lib/", "core/", "packages/"]

# ── plan-related files ──────────────────────────────────────────
PLAN_FILES = {"plan.md", "plan.meta.json", "PLAN.md", "PLAN_META.json"}

# ── restricted commit verbs ─────────────────────────────────────
RESTRICTED_COMMANDS = [
    "git commit", "git merge", "git push",
    "release", "assembleRelease", "publish"
]

# ── long documents (orchestrator must not copy verbatim) ────────
LONG_DOCS = {
    "plan.md", "PLAN.md",
    "implementation.md", "IMPLEMENTATION.md",
    "test-report.md", "TEST_REPORT.md",
    "review.md", "REVIEW.md",
    "independent-review.md", "INDEPENDENT_REVIEW.md"
}

# ── dev keywords for UserPromptSubmit auto-init ─────────────────
DEV_KEYWORDS = [
    "auto-dev", "auto_dev", "开发", "修复", "重构",
    "实现", "测试", "auto dev", "multi-agent", "multi_agent"
]

# ── STATE.json schema (template) ─────────────────────────────────
STATE_SCHEMA = {
    "task_id": "",
    "current_phase": "intake",
    "orchestrator": "",
    "planner_owner": "codex-planner",
    "plan_status": "pending",
    "plan_file": "",
    "plan_meta_file": "",
    "current_category": "",
    "current_wave": 0,
    "allowed_next_actions": [],
    "last_output_file": "",
    "next_input_file": "",
    "verification_status": "pending",
    "created_at": "",
    "updated_at": ""
}


def load_json(path):
    """Load JSON, return {} if missing or invalid."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_state(state_dir):
    """Load STATE.json from the state directory."""
    state_path = os.path.join(state_dir, "STATE.json")
    return load_json(state_path)


def load_plan_meta(state):
    """Load plan.meta.json if plan_meta_file is set in state."""
    meta_path = state.get("plan_meta_file", "")
    if meta_path and os.path.exists(meta_path):
        return load_json(meta_path)
    # try next to plan_file
    plan_file = state.get("plan_file", "")
    if plan_file:
        meta_path = os.path.join(os.path.dirname(plan_file), "plan.meta.json")
        return load_json(meta_path)
    return {}


def is_source_path(file_path):
    """Check if file_path is under a source directory."""
    normalized = file_path.replace("\\", "/").lower()
    for sd in SOURCE_DIRS:
        if normalized.startswith(sd.lower()):
            return True
    return False


def is_plan_file(file_path):
    """Check if file_path is a plan file (plan.md or plan.meta.json)."""
    name = os.path.basename(file_path).lower()
    return name in PLAN_FILES


def is_long_doc(file_path):
    """Check if file_path is a long document orchestrator must not copy."""
    name = os.path.basename(file_path).lower()
    return name in LONG_DOCS


def has_verification(state_dir):
    """Check if verification report exists and is valid."""
    report_path = os.path.join(state_dir, "verification-report.md")
    if not os.path.exists(report_path):
        return False, "verification-report.md not found"

    content = Path(report_path).read_text(encoding="utf-8", errors="ignore")
    checks = {
        "VERIFIED_COMMIT": "VERIFIED_COMMIT" in content,
        "VERIFICATION_COMMAND": "VERIFICATION_COMMAND" in content,
        "EXIT_CODE = 0": "EXIT_CODE" in content and "0" in content.split("EXIT_CODE", 1)[-1][:30] if "EXIT_CODE" in content else False,
        "RESULT_FILE": "RESULT_FILE" in content,
    }
    missing = [k for k, v in checks.items() if not v]
    if missing:
        return False, f"verification-report.md missing: {', '.join(missing)}"

    state = load_state(state_dir)
    if state.get("verification_status") != "passed":
        return False, "verification_status is not 'passed'"

    return True, "ok"


# ═══════════════════════════════════════════════════════════════════
#  GATE 1: No source edits before plan is approved
# ═══════════════════════════════════════════════════════════════════
def gate_no_edit_without_plan(hook_input, state, state_dir):
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return True, ""

    file_path = hook_input.get("file_path", "") or hook_input.get("path", "")
    if not is_source_path(file_path):
        return True, ""

    current_phase = state.get("current_phase", "intake")
    if current_phase not in ("development", "fixing", "testing"):
        return False, (
            f"GATE 1 BLOCKED: current_phase={current_phase} — "
            f"源码编辑只允许在 development/fixing/testing 阶段。"
        )

    if state.get("plan_status") != "approved":
        return False, (
            f"GATE 1 BLOCKED: plan_status={state.get('plan_status')} — "
            f"计划未批准前不能修改源码。"
        )

    plan_file = state.get("plan_file", "")
    if not plan_file or not os.path.exists(plan_file):
        return False, "GATE 1 BLOCKED: plan_file 不存在。"

    plan_meta = load_plan_meta(state)
    if not plan_meta:
        return False, "GATE 1 BLOCKED: plan.meta.json 不存在。"

    allowed_planners = {"codex-planner", "codex", "planner"}
    if plan_meta.get("created_by", "") not in allowed_planners:
        return False, (
            f"GATE 1 BLOCKED: plan.meta.json.created_by="
            f"{plan_meta.get('created_by')}，不是 codex-planner。"
        )

    if plan_meta.get("plan_status") != "approved":
        return False, (
            f"GATE 1 BLOCKED: plan.meta.json.plan_status="
            f"{plan_meta.get('plan_status')}，不是 approved。"
        )

    return True, ""


# ═══════════════════════════════════════════════════════════════════
#  GATE 2: Orchestrator cannot write plan files directly
# ═══════════════════════════════════════════════════════════════════
def gate_orchestrator_no_plan_write(hook_input, state, state_dir):
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return True, ""

    file_path = hook_input.get("file_path", "") or hook_input.get("path", "")
    if not is_plan_file(file_path):
        return True, ""

    # In Claude Code hooks, we can't directly know "who is calling"
    # We infer from the state: if state says orchestrator is active, block
    # For now, always block direct plan.md writes — they must go through planner
    return False, (
        "GATE 2 BLOCKED: 主编排者不能直接写 plan.md 或 plan.meta.json。"
        "正式计划必须由 planner_owner (" + state.get("planner_owner", "codex-planner") + ") 生成。"
        "主编排者只能生成 plan-input.md、REQUIREMENTS.md、CODE_CONTEXT.md、DECISIONS.md。"
    )


# ═══════════════════════════════════════════════════════════════════
#  GATE 3: No commit/merge/push/release without verification
# ═══════════════════════════════════════════════════════════════════
def gate_no_commit_without_verification(hook_input, state, state_dir):
    command = hook_input.get("command", "") or hook_input.get("bash_command", "")
    if not command:
        return True, ""

    cmd_lower = command.lower()
    is_restricted = any(rc in cmd_lower for rc in RESTRICTED_COMMANDS)
    is_done_transition = (
        "STATE.json" in command and
        ("done" in cmd_lower or '"done"' in command)
    )

    if not is_restricted and not is_done_transition:
        return True, ""

    ok, reason = has_verification(state_dir)
    if not ok:
        return False, f"GATE 3 BLOCKED: {reason} 请先完成验证再提交/合并/发布。"

    return True, ""


# ═══════════════════════════════════════════════════════════════════
#  GATE 4: Orchestrator must not copy long documents verbatim
# ═══════════════════════════════════════════════════════════════════
# This gate is informational — it warns but doesn't block,
# because detecting "copying" is hard at the tool level.
# Instead, it blocks Write/Edit to files that ARE long documents
# (preventing accidental overwrite), and relies on prompt enforcement.
def gate_orchestrator_no_long_doc_copy(hook_input, state, state_dir):
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return True, ""

    file_path = hook_input.get("file_path", "") or hook_input.get("path", "")
    if not is_long_doc(file_path):
        return True, ""

    # These files should only be written by their original agents
    return False, (
        f"GATE 4 BLOCKED: {os.path.basename(file_path)} 是只读产物文件。"
        f"主编排者不得覆盖。由原责任代理维护。"
    )


# ═══════════════════════════════════════════════════════════════════
#  PreToolUse dispatcher
# ═══════════════════════════════════════════════════════════════════
def handle_pretooluse(hook_input, state, state_dir):
    gates = [
        ("GATE_1", gate_no_edit_without_plan),
        ("GATE_2", gate_orchestrator_no_plan_write),
        ("GATE_3", gate_no_commit_without_verification),
        ("GATE_4", gate_orchestrator_no_long_doc_copy),
    ]

    for gate_name, gate_fn in gates:
        allowed, reason = gate_fn(hook_input, state, state_dir)
        if not allowed:
            return {
                "decision": "deny",
                "reason": reason,
                "hook_type": "pretooluse",
                "gate": gate_name,
                "checked_at": datetime.now().isoformat()
            }

    return {
        "decision": "allow",
        "reason": "all gates passed",
        "hook_type": "pretooluse",
        "checked_at": datetime.now().isoformat()
    }


# ═══════════════════════════════════════════════════════════════════
#  Stop Hook — lightweight reminder
# ═══════════════════════════════════════════════════════════════════
def handle_stop(hook_input, state, state_dir):
    current_phase = state.get("current_phase", "intake")
    verification_status = state.get("verification_status", "pending")

    warnings = []

    if current_phase != "done" and current_phase != "blocked":
        warnings.append(f"当前阶段: {current_phase}，不是 done。任务未完成。")

    if verification_status != "passed":
        warnings.append("当前任务还没有有效的验证报告。请勿宣称完成。")

    if hook_input.get("stop_reason", "") == "end_turn":
        warnings.append("响应结束。如有未完成工作，下次继续。")

    if warnings:
        return {
            "decision": "allow",
            "reason": " | ".join(warnings),
            "hook_type": "stop",
            "warning": True
        }

    return {
        "decision": "allow",
        "reason": "ok",
        "hook_type": "stop"
    }


# ═══════════════════════════════════════════════════════════════════
#  UserPromptSubmit Hook — auto-init state
# ═══════════════════════════════════════════════════════════════════
def handle_userpromptsubmit(hook_input, state, state_dir):
    prompt = hook_input.get("prompt", "") or hook_input.get("text", "")
    prompt_lower = prompt.lower()

    triggered = any(kw.lower() in prompt_lower for kw in DEV_KEYWORDS)
    if not triggered:
        return {"decision": "allow", "reason": "no dev keywords", "hook_type": "userpromptsubmit"}

    # Check if state already exists
    state_path = os.path.join(state_dir, "STATE.json")
    if os.path.exists(state_path):
        reminder = (
            "auto-dev 提醒：先判断是否需要调研；"
            "未批准计划前不得修改源码；"
            "计划必须由指定 planner 生成；"
            "子代理之间通过路径交接；"
            "主编排者只记录状态，不搬运全文。"
        )
        return {
            "decision": "allow",
            "reason": reminder,
            "hook_type": "userpromptsubmit",
            "state_exists": True
        }

    # Initialize state
    init_state = dict(STATE_SCHEMA)
    init_state["created_at"] = datetime.now().isoformat()
    init_state["updated_at"] = datetime.now().isoformat()

    os.makedirs(state_dir, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(init_state, f, indent=2, ensure_ascii=False)

    runs_dir = os.path.join(state_dir, "runs")
    os.makedirs(runs_dir, exist_ok=True)

    return {
        "decision": "allow",
        "reason": (
            f"auto-dev 已初始化。当前阶段: intake。"
            f"STATE.json 已创建于 {state_path}。"
            f"提醒：先调研 → Codex planner 出计划 → 批准后开发。"
        ),
        "hook_type": "userpromptsubmit",
        "state_exists": False
    }


# ═══════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════
def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "decision": "deny",
            "reason": f"Usage: {sys.argv[0]} <hook_type> <state_dir>",
            "hook_type": "unknown"
        }))
        sys.exit(1)

    hook_type = sys.argv[1].lower()
    state_dir = sys.argv[2]

    hook_input = {}
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    state = load_state(state_dir)

    handlers = {
        "pretooluse": handle_pretooluse,
        "stop": handle_stop,
        "userpromptsubmit": handle_userpromptsubmit,
    }

    handler = handlers.get(hook_type)
    if not handler:
        print(json.dumps({
            "decision": "allow",
            "reason": f"unknown hook_type: {hook_type}",
            "hook_type": hook_type
        }))
        sys.exit(0)

    result = handler(hook_input, state, state_dir)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("decision") == "allow" else 1)


if __name__ == "__main__":
    main()
