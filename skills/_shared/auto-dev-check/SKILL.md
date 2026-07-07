---
name: auto-dev-check
description: 检查 auto-dev Skill、Claude 子智能体、Codex CLI、Git 与可选 Android Emulator 环境是否可用，不修改业务代码。
disable-model-invocation: true
allowed-tools: Read Glob Grep Bash
---

# Auto Dev 环境检查

从项目根目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PROJECT_DIR}/scripts/auto-code-android-dev/check-environment.ps1" -ProjectRoot "${CLAUDE_PROJECT_DIR}"
```

读取 `.ai/ENVIRONMENT_REPORT.md` 并汇报：

- 全局 `auto-dev`（`../auto-dev/SKILL.md`）和项目包装层是否存在；
- Claude Code、Codex、Git 是否可调用；
- Codex 是否登录；
- 当前项目是否是 Android 项目；
- `adb`、`emulator` 与 AVD 是否可用；
- 项目包装脚本是否具备 Codex 运行可观测性（前台运行、`status.json`、stdout/stderr 日志、静默超时状态）；
- 哪些问题阻塞 `/auto-dev`，哪些只阻塞模拟器门禁。

不得自动下载 SDK、安装 Android Studio、创建 AVD、登录账号或修改业务代码。
