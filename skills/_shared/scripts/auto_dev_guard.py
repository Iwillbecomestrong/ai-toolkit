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
import re


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

READ_ONLY_BASH_PATTERNS = [
    "rg ", "rg.exe ", "grep ", "findstr ", "select-string ",
    "get-content ", "type ", "cat ", "less ", "more ",
    "get-childitem", "ls ", "dir ", "pwd", "git status", "git diff"
]

PLAN_AGENT_COMMAND_PATTERNS = [
    "run-deepseek-plan",
    "run-deepseek-review",
    "deepseek-v4-pro",
    "run-codex-plan.ps1",
    "run-codex-plan",
    "run-opencode-plan",
    "run-omo-plan",
    "hyperplan",
    "omo hyperplan",
    "oh-my-openagent",
]

# ── dev keywords for UserPromptSubmit auto-init ─────────────────
DEV_KEYWORDS = [
    "auto-dev", "auto_dev", "开发", "修复", "重构",
    "实现", "测试", "auto dev", "multi-agent", "multi_agent"
]

# ── bug report keywords — force rework → plan agent cycle ──────
BUG_REPORT_KEYWORDS = [
    "闪退", "崩溃", "crash", "报错", "错误", "不行", "不对",
    "没改好", "还是", "还有问题", "没修复", "仍然", "依旧",
    "bug", "BUG", "Bug", "不工作", "不能用", "坏了",
    "太小", "太大", "空白", "空隙", "看不见", "显示不全",
    "滚动不了", "点不了", "没反应", "卡住",
]

# ── STATE.json schema (template) ─────────────────────────────────
STATE_SCHEMA = {
    "task_id": "",
    "current_phase": "intake",
    "orchestrator": "",
    "planner_owner": "deepseek-v4-pro-planner",
    "plan_status": "pending",
    "plan_file": "",
    "plan_meta_file": "",
    "plan_reviewer": "gpt-5.4-plan-reviewer",
    "plan_review_status": "pending",
    "plan_review_file": "",
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


def project_root_from_state_dir(state_dir):
    """Infer project root from configured state dir (.ai-work / .collab-work)."""
    return str(Path(state_dir).resolve().parent)


def parse_status_markdown(status_path):
    """Parse simple `STATUS.md` bullet fields into a dict."""
    try:
        content = Path(status_path).read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return {}

    fields = {}
    pattern = re.compile(r"^- `([^`]+)`\s*(.+)?$", re.MULTILINE)
    for match in pattern.finditer(content):
        raw_key = match.group(1).strip()
        raw_value = (match.group(2) or "").strip()
        key = raw_key.rstrip(":").strip()
        value = raw_value.strip()
        if value.startswith("`") and value.endswith("`") and len(value) >= 2:
            value = value[1:-1]
        fields[key] = value
    return fields


def is_terminal_task_stage(stage):
    """Best-effort terminal stage detection for .ai/tasks STATUS.md."""
    stage_upper = (stage or "").upper()
    terminal_markers = ["COMPLETE", "COMPLETED", "DONE", "BLOCKED", "WAITING_USER_ACCEPTANCE"]
    return any(marker in stage_upper for marker in terminal_markers)


def discover_active_task_context(state_dir):
    """Discover latest active .ai/tasks task when legacy STATE.json is absent."""
    project_root = Path(project_root_from_state_dir(state_dir))
    tasks_root = project_root / ".ai" / "tasks"
    if not tasks_root.exists():
        return None

    candidates = []
    for task_dir in tasks_root.iterdir():
        if not task_dir.is_dir():
            continue
        status_path = task_dir / "STATUS.md"
        if not status_path.exists():
            continue
        status_fields = parse_status_markdown(status_path)
        current_stage = status_fields.get("current_stage", "")
        candidates.append({
            "task_dir": str(task_dir),
            "status_path": str(status_path),
            "task_id": status_fields.get("task_id", task_dir.name),
            "current_stage": current_stage,
            "has_plan_file": (task_dir / "PLAN.md").exists(),
            "has_plan_review_file": (task_dir / "PLAN_REVIEW.md").exists() or (task_dir / "PLAN_REVIEW.round1.gpt-5.4.md").exists() or (task_dir / "PLAN_REVIEW.round2.gpt-5.5.md").exists() or (task_dir / "plan-review.meta.json").exists(),
            "has_deferred_codex_review_file": (task_dir / "DEFERRED_CODEX_REVIEW.md").exists(),
            "has_current_codex_run": (task_dir / "CURRENT_CODEX_RUN.json").exists(),
            "is_terminal": is_terminal_task_stage(current_stage),
            "last_write_time": task_dir.stat().st_mtime,
        })

    if not candidates:
        return None

    non_terminal = [c for c in candidates if not c["is_terminal"]]
    selected = sorted(non_terminal or candidates, key=lambda item: item["last_write_time"], reverse=True)[0]
    return selected


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


def has_deferred_codex_review_record(state, plan_meta, state_dir):
    """Check whether Codex plan review was explicitly deferred due to quota."""
    candidate_paths = [
        state.get("deferred_codex_review_file", ""),
        state.get("codex_deferred_review_file", ""),
        plan_meta.get("deferred_codex_review_file", ""),
        plan_meta.get("codex_deferred_review_file", ""),
    ]

    plan_file = state.get("plan_file") or plan_meta.get("plan_file") or ""
    if plan_file:
        candidate_paths.append(os.path.join(os.path.dirname(plan_file), "DEFERRED_CODEX_REVIEW.md"))

    candidate_paths.append(os.path.join(state_dir, "DEFERRED_CODEX_REVIEW.md"))

    return any(path and os.path.exists(path) for path in candidate_paths)


def is_source_path(file_path):
    """Check if file_path is under a source directory.

    Claude Code / OpenCode hooks may pass either project-relative paths
    (``app/src/...``) or absolute paths (``G:/repo/app/src/...``).
    Treat both forms as source paths.
    """
    normalized = (file_path or "").replace("\\", "/").lower().lstrip("./")
    for sd in SOURCE_DIRS:
        sd_norm = sd.lower().strip("/")
        if normalized == sd_norm or normalized.startswith(sd_norm + "/"):
            return True
        if ("/" + sd_norm + "/") in normalized:
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


def is_plan_agent_command(command):
    """Check whether a bash command is invoking an approved plan-agent wrapper."""
    cmd_lower = (command or "").replace("\\", "/").lower()
    return any(pattern in cmd_lower for pattern in PLAN_AGENT_COMMAND_PATTERNS)


def is_read_only_bash_command(command):
    """Allow obvious read-only inspection commands before plan generation."""
    cmd_lower = (command or "").replace("\\", "/").lower().strip()
    return any(pattern in cmd_lower for pattern in READ_ONLY_BASH_PATTERNS)


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

    allowed_planners = {
        "deepseek-v4-pro-planner", "deepseek-v4-pro", "opencode-deepseek-planner",
        "codex-planner", "codex", "planner",
        "opencode-planner", "omo-planner", "opencode-omo-hyperplan"
    }
    if plan_meta.get("created_by", "") not in allowed_planners:
        return False, (
            f"GATE 1 BLOCKED: plan.meta.json.created_by="
            f"{plan_meta.get('created_by')}，不是允许的计划代理。"
        )

    if plan_meta.get("plan_status") != "approved":
        return False, (
            f"GATE 1 BLOCKED: plan.meta.json.plan_status="
            f"{plan_meta.get('plan_status')}，不是 approved。"
        )

    plan_review_status = state.get("plan_review_status") or plan_meta.get("plan_review_status")
    if plan_review_status == "approved":
        plan_review_file = state.get("plan_review_file") or plan_meta.get("plan_review_file") or plan_meta.get("review_file")
        if not plan_review_file:
            return False, "GATE 1 BLOCKED: plan_review_file 未记录；GPT/Codex 有额度时必须产出 PLAN_REVIEW.round1.gpt-5.4.md 或 PLAN_REVIEW.md。"
        if plan_review_file and not os.path.exists(plan_review_file):
            return False, f"GATE 1 BLOCKED: plan_review_file 不存在: {plan_review_file}"
        return True, ""

    if plan_review_status == "rework_pending":
        return False, (
            "GATE 1 BLOCKED: 用户反馈了 bug/问题，STATE 已回退到 planning。"
            "源码编辑被阻断。必须先：\n"
            "  ① 写 plan-input.md 或 PLAN_PATCH.md（描述根因+方案）\n"
            "  ② 用 Agent 工具 dispatch DeepSeek V4 Pro planner 审查/生成修订计划\n"
            "  ③ 计划审查通过（plan_review_status=approved）\n"
            "  ④ 用 Agent 工具 dispatch developer 子代理改代码\n"
            "主编排者不得直接改源码——谁开发谁修，主编排只负责协调。"
        )

    if plan_review_status in ("deferred_due_to_codex_quota", "deferred_due_to_quota"):
        if has_deferred_codex_review_record(state, plan_meta, state_dir):
            return True, ""
        return False, (
            "GATE 1 BLOCKED: Codex 二次计划审查被标记为额度延期，"
            "但没有找到 DEFERRED_CODEX_REVIEW.md。"
        )

    return False, (
        f"GATE 1 BLOCKED: plan_review_status={plan_review_status} — "
        "Codex 二次计划审查既未通过，也未记录额度延期。"
    )


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

    return False, (
        "GATE 2 BLOCKED: 主编排者不能直接写 plan.md 或 plan.meta.json。"
        "正式计划必须由计划代理生成：默认 DeepSeek V4 Pro planner，或 OpenCode/oh-my-openagent hyperplan。"
        "主编排者只能生成 plan-input.md、REQUIREMENTS.md、CODE_CONTEXT.md、DECISIONS.md。"
    )


# ═══════════════════════════════════════════════════════════════════
#  GATE 3: No merge/push/release/done without final verification
# ═══════════════════════════════════════════════════════════════════
def gate_no_commit_without_verification(hook_input, state, state_dir):
    """Block finalization actions without a final verification report.

    Ordinary step commits are intentionally allowed: commit_step_gate requires
    agents to commit atomic edits early, before final verification exists. Final
    verification is required for merge/push/release/publish/STATE done.
    """
    command = hook_input.get("command", "") or hook_input.get("bash_command", "")
    if not command:
        return True, ""

    cmd_lower = command.lower()
    finalization_triggers = [
        "git merge", "git push", "release", "assemblerelease", "publish"
    ]
    is_finalization = any(rc in cmd_lower for rc in finalization_triggers)
    is_done_transition = (
        "state.json" in cmd_lower and
        ("done" in cmd_lower or '"done"' in command)
    )

    # Do not block ordinary step commits. Gate 5 handles working-tree hygiene.
    if not is_finalization and not is_done_transition:
        return True, ""

    ok, reason = has_verification(state_dir)
    if not ok:
        return False, f"GATE 3 BLOCKED: {reason} 请先完成最终验证再合并/发布/标记 done。"

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
#  GATE 5: Working tree hygiene - prevent accumulating uncommitted changes
# ═══════════════════════════════════════════════════════════════════
# Prevents the failure mode where Agent modifies 100+ lines and then
# session/linter/editor interruption wipes out the entire working tree.
# Triggers: 任何 git commit/push/merge 前, 检查 working tree 是否有未相关改动
def gate_working_tree_hygiene(hook_input, state, state_dir):
    """Prevent unsafe git operations with dirty unrelated working tree.

    Rules:
    - Reject `git add .` and `git add -A` because they pull unrelated files.
    - Before commit/merge/push/release, reject unstaged tracked changes and
      untracked files. Staged changes are allowed for ordinary step commits.
    - Use project root inferred from state_dir when state.project_root is absent.
    """
    import subprocess
    command = hook_input.get("command", "") or hook_input.get("bash_command", "")
    if not command:
        return True, ""

    cmd_lower = command.lower()
    triggers = ["git commit", "git push", "git merge", "release ", "assemblerelease", "publish"]
    if not any(t in cmd_lower for t in triggers):
        return True, ""

    if re.search(r"git\s+add\s+(\.|-A|--all)(\s|$)", command):
        return False, (
            "GATE 5 BLOCKED: 禁止使用 git add . / git add -A / git add --all。"
            "请精确 git add <file>，避免带入无关文件。"
        )

    project_root = state.get("project_root") or project_root_from_state_dir(state_dir)
    if not project_root or not os.path.isdir(project_root):
        return True, ""

    try:
        unstaged = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if unstaged.returncode != 0 or untracked.returncode != 0:
            return True, ""

        dirty = []
        dirty.extend([f" M {x}" for x in unstaged.stdout.splitlines() if x.strip()])
        dirty.extend([f"?? {x}" for x in untracked.stdout.splitlines() if x.strip()])

        if dirty:
            return False, (
                "GATE 5 BLOCKED: working tree 有未暂存或未跟踪改动:\n" +
                "\n".join(f"  {line}" for line in dirty[:20]) +
                "\n请先精确 git add + git commit，或 git restore / git clean，或让用户决定 pre-existing 改动。"
            )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return True, ""


def gate_task_source_edit_requires_plan_agent(hook_input, task_context):
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return True, ""

    file_path = hook_input.get("file_path", "") or hook_input.get("path", "")
    if not is_source_path(file_path):
        return True, ""

    if task_context.get("has_plan_file") and (
        task_context.get("has_plan_review_file") or task_context.get("has_deferred_codex_review_file")
    ):
        return True, ""

    if not task_context.get("has_plan_file"):
        return False, (
            f"TASK GATE BLOCKED: 当前活跃任务 {task_context.get('task_id')} 还没有计划代理生成的 PLAN.md。"
            "请先运行 DeepSeek V4 Pro planner / run-opencode-plan / OMO hyperplan。"
        )

    return False, (
        f"TASK GATE BLOCKED: 当前活跃任务 {task_context.get('task_id')} 还没有通过 Codex 二次计划审查，也没有记录 Codex 额度延期。"
        "请先产出 PLAN_REVIEW.round1.gpt-5.4.md / PLAN_REVIEW.md / plan-review.meta.json，或写 DEFERRED_CODEX_REVIEW.md。"
    )


def gate_task_bash_requires_plan_agent(hook_input, task_context):
    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Bash":
        return True, ""

    if task_context.get("has_plan_file") and (
        task_context.get("has_plan_review_file") or task_context.get("has_deferred_codex_review_file")
    ):
        return True, ""

    command = hook_input.get("command", "") or hook_input.get("bash_command", "")
    if not command:
        return True, ""

    if is_plan_agent_command(command):
        return True, ""

    if is_read_only_bash_command(command):
        return True, ""

    return False, (
        f"TASK GATE BLOCKED: 当前活跃任务 {task_context.get('task_id')} 缺少 PLAN.md 或 PLAN_REVIEW.round1.gpt-5.4.md / PLAN_REVIEW.md / DEFERRED_CODEX_REVIEW.md。"
        f"在继续执行非只读命令前，必须先生成 PLAN.md，并完成 Codex 审查或记录额度延期。"
    )


def gate_task_agent_requires_plan_agent_script(hook_input, task_context):
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Agent", "SendMessage"):
        return True, ""

    if task_context.get("has_plan_file") and (
        task_context.get("has_plan_review_file") or task_context.get("has_deferred_codex_review_file")
    ):
        return True, ""

    return False, (
        f"TASK GATE BLOCKED: 当前活跃任务 {task_context.get('task_id')} 还没有 PLAN.md 或 PLAN_REVIEW.round1.gpt-5.4.md / PLAN_REVIEW.md / DEFERRED_CODEX_REVIEW.md。"
        "禁止用普通 Agent/SendMessage 后台代替正式计划；Codex 无额度时必须记录延期审查。"
    )


# ═══════════════════════════════════════════════════════════════════
#  PreToolUse dispatcher
# ═══════════════════════════════════════════════════════════════════
def is_legacy_auto_dev_active(state, state_dir):
    """Check if legacy auto-dev STATE.json mode is currently active."""
    state_path = os.path.join(state_dir, "STATE.json")
    if not os.path.exists(state_path):
        return False
    if not state or not state.get("task_id"):
        return False
    return True


def is_auto_dev_active(state, state_dir):
    """Check if any supported auto-dev mode is active."""
    if is_legacy_auto_dev_active(state, state_dir):
        return True
    return discover_active_task_context(state_dir) is not None


def handle_pretooluse(hook_input, state, state_dir):
    legacy_active = is_legacy_auto_dev_active(state, state_dir)
    task_context = None if legacy_active else discover_active_task_context(state_dir)

    # Only apply gates when auto-dev is actively running
    if not legacy_active and not task_context:
        return {"decision": "allow", "reason": "auto-dev not active — guard skipped", "hook_type": "pretooluse"}

    if task_context:
        gates = [
            ("TASK_GATE_PLAN_AGENT", lambda hook, _state, _state_dir: gate_task_agent_requires_plan_agent_script(hook, task_context)),
            ("TASK_GATE_PLAN_BASH", lambda hook, _state, _state_dir: gate_task_bash_requires_plan_agent(hook, task_context)),
            ("TASK_GATE_PLAN_EDIT", lambda hook, _state, _state_dir: gate_task_source_edit_requires_plan_agent(hook, task_context)),
            ("GATE_2", gate_orchestrator_no_plan_write),
            ("GATE_4", gate_orchestrator_no_long_doc_copy),
            ("GATE_5", gate_working_tree_hygiene),
        ]
    else:
        gates = [
            ("GATE_1", gate_no_edit_without_plan),
            ("GATE_2", gate_orchestrator_no_plan_write),
            ("GATE_3", gate_no_commit_without_verification),
            ("GATE_4", gate_orchestrator_no_long_doc_copy),
            ("GATE_5", gate_working_tree_hygiene),
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
    # Only remind when auto-dev is actively running
    task_context = discover_active_task_context(state_dir)
    if not is_auto_dev_active(state, state_dir):
        return {"decision": "allow", "reason": "auto-dev not active", "hook_type": "stop"}

    if not is_legacy_auto_dev_active(state, state_dir) and task_context:
        current_stage = task_context.get("current_stage", "unknown")
        if task_context.get("has_current_codex_run"):
            runtime_hint = "当前任务已有 CURRENT_CODEX_RUN.json，可优先据此恢复计划/审查运行状态。"
        else:
            runtime_hint = "当前任务还没有 CURRENT_CODEX_RUN.json；若正在补计划，优先检查是否已运行 DeepSeek/OMO plan 或 review 入口。"
        return {
            "decision": "allow",
            "reason": f"当前任务阶段: {current_stage}。{runtime_hint}",
            "hook_type": "stop",
            "warning": True,
        }

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

    # ── 优先检测：用户反馈 bug → 强制回退 STATE 到 planning ──
    is_bug_report = any(kw.lower() in prompt_lower for kw in BUG_REPORT_KEYWORDS)
    state_path = os.path.join(state_dir, "STATE.json")

    if is_bug_report and os.path.exists(state_path):
        current_state = load_json(state_path)
        current_phase = current_state.get("current_phase", "")
        current_plan_review = current_state.get("plan_review_status", "")

        # 只在 auto-dev 活跃且当前不在 planning/intake 时强制回退
        if current_phase and current_phase not in ("intake", "done", "blocked"):
            current_state["current_phase"] = "planning"
            current_state["plan_review_status"] = "rework_pending"
            current_state["plan_status"] = "pending"
            current_state["updated_at"] = datetime.now().isoformat()
            current_state["_rework_triggered_by"] = "UserPromptSubmit bug-report detection"
            current_state["_rework_user_message"] = prompt[:200]

            os.makedirs(state_dir, exist_ok=True)
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(current_state, f, indent=2, ensure_ascii=False)

            return {
                "decision": "allow",
                "reason": (
                    f"⛔ 检测到用户反馈 bug/问题 → STATE 已强制回退到 planning。"
                    f"plan_review_status = rework_pending（Gate 1 将阻断所有源码编辑）。"
                    f"必须先：① 写 plan-input.md / PLAN_PATCH.md → "
                    f"② DeepSeek V4 Pro planner 审查/生成修订计划 → "
                    f"③ plan_review 通过 → ④ dispatch developer 子代理改代码。"
                    f"主编排者不得直接改源码。当前 phase={current_phase} → planning。"
                ),
                "hook_type": "userpromptsubmit",
                "rework_triggered": True
            }

    triggered = any(kw.lower() in prompt_lower for kw in DEV_KEYWORDS)
    if not triggered:
        return {"decision": "allow", "reason": "no dev keywords", "hook_type": "userpromptsubmit"}

    active_task = discover_active_task_context(state_dir)
    if active_task:
        reminder = (
            f"auto-dev 任务模式提醒：当前活跃任务 {active_task.get('task_id')}，"
            f"阶段 {active_task.get('current_stage') or 'unknown'}。"
            "若缺少 PLAN.md 或 PLAN_REVIEW.round1.gpt-5.4.md / DEFERRED_CODEX_REVIEW.md，下一步必须先运行计划入口，并完成 GPT/Codex 审查或记录额度延期。"
        )
        return {
            "decision": "allow",
            "reason": reminder,
            "hook_type": "userpromptsubmit",
            "state_exists": False
        }

    # Check if legacy state already exists
    state_path = os.path.join(state_dir, "STATE.json")
    if os.path.exists(state_path):
        reminder = (
            "auto-dev 提醒：先判断是否需要调研；"
            "未批准计划前不得修改源码；"
            "计划必须由指定 planner 生成；Codex 审查有额度则通过，无额度则记录延期；"
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
            f"提醒：先调研 → DeepSeek 出计划 → Codex 审查或记录额度延期 → 再开发。"
        ),
        "hook_type": "userpromptsubmit",
        "state_exists": False
    }


# ═══════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════
def main():
    # Suppress stderr — Claude Code hook reads stdout as JSON, any stderr breaks parsing
    sys.stderr = open(os.devnull, 'w')

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
    # Claude Code hook expects {"continue": true/false}
    if result.get("decision") == "allow":
        print(json.dumps({"continue": True}, ensure_ascii=False))
    else:
        print(json.dumps({"continue": False, "reason": result.get("reason", "blocked")}, ensure_ascii=False))
    sys.exit(0 if result.get("decision") == "allow" else 1)


if __name__ == "__main__":
    main()
