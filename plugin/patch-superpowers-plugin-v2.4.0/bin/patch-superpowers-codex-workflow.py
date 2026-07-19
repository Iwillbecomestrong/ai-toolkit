#!/usr/bin/env python3
"""为 Sol/Luna 角色构造并执行显式模型的 Codex CLI 命令。

所有新会话和恢复会话都必须显式传入：
- `-m <exact-model-id>`
- `-c model_reasoning_effort="<effort>"`

这样不会回退到 Codex CLI 的默认模型或默认推理强度。
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "model-routing.json"
ALLOWED_EFFORTS = {"low", "medium", "high", "xhigh"}


class WorkflowError(RuntimeError):
    pass


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise WorkflowError("config 根节点必须是对象")
    if not isinstance(data.get("codex_cli_roles"), dict):
        raise WorkflowError("config 缺少 codex_cli_roles")
    return data


def _reasoning_override(effort: str) -> str:
    if effort not in ALLOWED_EFFORTS:
        raise WorkflowError(f"不支持的 reasoning effort: {effort}")
    return f'model_reasoning_effort="{effort}"'


def role_route(config: dict[str, Any], role: str, effort: str | None = None) -> dict[str, str]:
    routes = config.get("codex_cli_roles", {})
    if role not in routes:
        raise WorkflowError(f"未知 Codex 角色: {role}")
    route = routes[role]
    model = str(route.get("model") or "").strip()
    selected_effort = str(effort or route.get("reasoning_effort") or "").strip()
    sandbox = str(route.get("sandbox") or "read-only").strip()
    if not model:
        raise WorkflowError(f"角色 {role} 缺少显式 model")
    if not selected_effort:
        raise WorkflowError(f"角色 {role} 缺少显式 reasoning_effort")
    _reasoning_override(selected_effort)
    return {"model": model, "reasoning_effort": selected_effort, "sandbox": sandbox}


def build_role_command(
    config: dict[str, Any],
    role: str,
    thread_id: str | None = None,
    effort: str | None = None,
) -> list[str]:
    """构造新会话或恢复会话命令；两者都显式指定 model/effort。"""
    route = role_route(config, role, effort)
    command = [
        "codex",
        "exec",
        "-m",
        route["model"],
        "-c",
        _reasoning_override(route["reasoning_effort"]),
        "--sandbox",
        route["sandbox"],
        "--json",
    ]
    if thread_id:
        if thread_id == "UNKNOWN":
            raise WorkflowError("恢复会话需要有效 thread_id")
        command.extend(["resume", thread_id, "-"])
    else:
        command.append("-")
    return command


def parse_jsonl(text: str) -> tuple[str, str]:
    thread_id = ""
    messages: list[str] = []
    errors: list[str] = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise WorkflowError(f"Codex JSONL 无效: {exc}: {raw[:160]}") from exc
        event_type = event.get("type")
        if event_type == "thread.started":
            thread_id = str(event.get("thread_id") or "")
        elif event_type == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message" and item.get("text"):
                messages.append(str(item["text"]))
        elif event_type in {"error", "turn.failed"}:
            errors.append(json.dumps(event, ensure_ascii=False))
    if errors:
        raise WorkflowError("Codex 返回失败事件:\n" + "\n".join(errors))
    if not messages:
        raise WorkflowError("Codex JSONL 中没有最终 agent_message")
    return thread_id, messages[-1]


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_role(
    *,
    config: dict[str, Any],
    role: str,
    prompt: str,
    cwd: Path,
    output_dir: Path,
    thread_id: str | None = None,
    effort: str | None = None,
) -> Path:
    route = role_route(config, role, effort)
    command = build_role_command(config, role, thread_id=thread_id, effort=effort)
    output_dir.mkdir(parents=True, exist_ok=True)
    stdout_file = output_dir / "stdout.jsonl"
    stderr_file = output_dir / "stderr.log"
    report_file = output_dir / "final-message.md"
    status_file = output_dir / "status.json"
    started_at = datetime.now(timezone.utc).isoformat()
    _write_json(status_file, {
        "status": "running",
        "role": role,
        "model": route["model"],
        "reasoning_effort": route["reasoning_effort"],
        "sandbox": route["sandbox"],
        "thread_id": thread_id or "",
        "started_at": started_at,
        "command": command,
        "stdout_file": str(stdout_file),
        "stderr_file": str(stderr_file),
        "output_file": str(report_file),
    })
    try:
        proc = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            cwd=cwd,
            check=False,
        )
        stdout_file.write_text(proc.stdout, encoding="utf-8")
        stderr_file.write_text(proc.stderr, encoding="utf-8")
        if proc.returncode != 0:
            raise WorkflowError(f"Codex CLI 退出码 {proc.returncode}，查看 {stderr_file}")
        returned_thread_id, final_message = parse_jsonl(proc.stdout)
        report_file.write_text(final_message.rstrip() + "\n", encoding="utf-8")
        _write_json(status_file, {
            "status": "completed",
            "role": role,
            "model": route["model"],
            "reasoning_effort": route["reasoning_effort"],
            "sandbox": route["sandbox"],
            "thread_id": returned_thread_id or thread_id or "",
            "started_at": started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "stdout_file": str(stdout_file),
            "stderr_file": str(stderr_file),
            "output_file": str(report_file),
        })
        return report_file
    except Exception as exc:
        _write_json(status_file, {
            "status": "failed",
            "role": role,
            "model": route["model"],
            "reasoning_effort": route["reasoning_effort"],
            "sandbox": route["sandbox"],
            "thread_id": thread_id or "",
            "started_at": started_at,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "error": str(exc),
            "stdout_file": str(stdout_file),
            "stderr_file": str(stderr_file),
            "output_file": str(report_file),
        })
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="显式模型的 Codex CLI 角色运行器")
    parser.add_argument("action", choices=["command", "run"])
    parser.add_argument("--role", required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--thread-id")
    parser.add_argument("--effort")
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    args = parser.parse_args()

    config = load_config(args.config)
    command = build_role_command(config, args.role, args.thread_id, args.effort)
    if args.action == "command":
        print(json.dumps(command, ensure_ascii=False))
        return 0
    if args.prompt_file is None or args.output_dir is None:
        parser.error("run 需要 --prompt-file 和 --output-dir")
    report = run_role(
        config=config,
        role=args.role,
        prompt=args.prompt_file.read_text(encoding="utf-8"),
        cwd=args.cwd.resolve(),
        output_dir=args.output_dir.resolve(),
        thread_id=args.thread_id,
        effort=args.effort,
    )
    print(f"CODEX_ROLE_OK={args.role}")
    print(f"OUTPUT_FILE={report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
