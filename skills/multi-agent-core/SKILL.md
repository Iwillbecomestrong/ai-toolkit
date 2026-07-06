---
name: multi-agent-core
description: 通用多智能体协作入口。用于把一组需求组织成澄清、调研、分类、受控并行开发、测试、验收与总回归。
argument-hint: "<需求、目标、Bug 现象或待办列表>"
disable-model-invocation: true
allowed-tools: Read Write Edit Glob Grep Bash Agent SendMessage
---

# Multi-Agent Core

> **共享核心**：通用规则、钩子、工作流、路由、报告格式见 `_shared/SKILL_CORE.md`。本文件仅定义 Codex / Reasonix 编排后端特有逻辑。
>
> **STATE_DIR**：`.collab-work`
>
> **强制门禁**：见 `_shared/HOOKS.md`。PreToolUse guard 脚本：`_shared/scripts/auto_dev_guard.py`

用户输入：

$ARGUMENTS

你是当前会话的**主编排者**。你负责理解用户真实目标、结合代码判断需求、发现歧义和隐藏约束、决定分类和并行波次，并对最终整体结果负责。

## 编排后端特有规则

**默认（无参数）**：本会话运行在 Codex（Codex A 编排），默认模型 `gpt-5.4`。

**`--orchestrator=reasonix`**：本会话运行在 Reasonix，编排者固定使用 **deepseekV4pro**；开发者使用 Codex 子代理（deepseekV4pro/flash 可选）；测试者使用 Codex 子代理（固定 deepseekV4flash）。Reasonix 编排者在本会话中直接做所有编排决策，Codex 只做执行。

## 入口规则

1. 解析 `$ARGUMENTS`：若含 `--orchestrator=reasonix`，设 `ORCHESTRATOR_BACKEND = reasonix`；否则默认 `codex`。
2. 若需求为空，暂停并要求补充。
3. 运行环境检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/multi-agent-core/check-environment.ps1" -ProjectRoot "."
```

4. 读取 `.collab/ENVIRONMENT_REPORT.md`。
5. 后续流程见 `_shared/SKILL_CORE.md`。

## 钩子自检（每次工具调用前）

在 Reasonix 中无系统级 PreToolUse hook，主编排者必须在每次 Write/Edit/MultiEdit 前自检：

```
□ 目标是否在 app/src/lib/core/packages/ 下？
  → current_phase 必须是 development/fixing/testing 且 plan_status = approved
□ 目标是否是 plan.md / plan.meta.json？
  → 主编排者禁止直接写，必须调用 Codex 子代理
□ 命令是否包含 git commit/merge/push？
  → 检查 verification-report.md 存在且 EXIT_CODE = 0
```

## 共享文件引用

- `_shared/SKILL_CORE.md` — 核心规则 + 钩子
- `_shared/HOOKS.md` — 完整门禁定义
- `_shared/WORKFLOW.md` — 状态机 + 角色模型
- `_shared/ROUTING.md` — 所有者路由
- `_shared/REPORT_FORMATS.md` — 报告模板
- `_shared/WORKTREE_GUIDE.md` — worktree 布局
- `_shared/SKILL_VERSIONING.md` — 版本管理规范
- `_shared/skills/*.md` — 8 个子阶段 skill
- `_shared/templates/*.md` — 模板
- `_shared/scripts/auto_dev_guard.py` — PreToolUse guard

## 项目专用扩展

Android 项目（如 IronWill）可使用 `auto-code-android-dev` 作为入口，它继承 `auto-dev` 的通用编排框架，同时引用本 skill 的多智能体协作规范。
