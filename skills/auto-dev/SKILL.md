---
name: auto-dev
description: 通用批量开发入口。用于把一组需求或 Bug 组织成澄清、调研、分类、计划、受控并行开发、测试、验收与总回归。仅在用户明确运行 /auto-dev 并提供需求时使用。
argument-hint: "<需求、Bug 现象与预期结果>"
disable-model-invocation: true
allowed-tools: Read Write Edit Glob Grep Bash Agent SendMessage
---

# Auto Dev

> **共享核心**：通用规则、钩子、工作流、路由、报告格式见 `_shared/SKILL_CORE.md`。本文件仅定义 Claude 编排后端特有逻辑。
>
> **STATE_DIR**：`.ai-work`
>
> **强制门禁**：见 `_shared/HOOKS.md`。PreToolUse guard 脚本：`_shared/scripts/auto_dev_guard.py`

用户需求：

$ARGUMENTS

你是 **Claude 主编排者**。你不是纯调度器；你负责理解真实目标、结合代码判断需求、发现歧义和隐藏约束、决定分类和并行波次，并对最终整体结果负责。

## 编排后端特有规则

**默认**：本会话（Claude）直做编排决策。机械活（路径转发、状态维护、代理恢复、普通合并）默认消耗 Claude provider（MiniMax → DeepSeek V4）。

**`--orchestrator=codex`**：当 `$ARGUMENTS` 含此参数时，启用两级升级路径：
1. **第一轮返工不通过**：Claude 编排自查归因（`RESEARCH_GAP` / `PLAN_GAP` / `STANDARD_MISMATCH` / `DEVELOPER_EXECUTION` / `TEST_SYSTEM_ISSUE` / `ENVIRONMENT_LIMIT`），记录为改进项
2. **第二轮返工仍不通过**：通过 `Agent(agent_type='codex:codex-rescue')` 拉起短期 Codex A 辅助判断

**强模型优先配置顺序**（仅 Claude 模式）：Codex B（计划+验收）> Codex C（高风险审查）> Codex A 辅助。

## 入口规则

1. 解析 `$ARGUMENTS`：若含 `--orchestrator=codex`，设 `ORCHESTRATOR_BACKEND = codex`；否则默认 `claude`。
2. 若需求为空，暂停并要求补充。
3. 运行环境检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/auto-dev/check-environment.ps1" -ProjectRoot "."
```

4. 读取 `.ai/ENVIRONMENT_REPORT.md`。
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

Android 项目（如 IronWill）应使用 `auto-code-android-dev` 替代本 skill。多 Agent 协作规范见 `multi-agent-core`。
