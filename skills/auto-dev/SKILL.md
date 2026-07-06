---
name: auto-dev
description: 通用批量开发入口。支持 Claude / Codex / Reasonix 三种编排后端，通过 --orchestrator= 参数切换。用于把一组需求或 Bug 组织成澄清、调研、分类、计划、受控并行开发、测试、验收与总回归。仅在用户明确运行 /auto-dev 并提供需求时使用。
argument-hint: "<需求、Bug 现象与预期结果> [--orchestrator=claude|codex|reasonix] [--project=android]"
disable-model-invocation: true
allowed-tools: Read Write Edit Glob Grep Bash Agent SendMessage
---

# Auto Dev

> **共享核心**：通用规则、钩子、工作流、路由、报告格式见 `_shared/SKILL_CORE.md`。
>
> **STATE_DIR**：`.ai-work`（通用）/ `.collab-work`（`--orchestrator=codex|reasonix` 默认时）
>
> **强制门禁**：见 `_shared/HOOKS.md`。PreToolUse guard：`_shared/scripts/auto_dev_guard.py`

用户需求：

$ARGUMENTS

你是当前会话的**主编排者**。你不是纯调度器；你负责理解真实目标、结合代码判断需求、发现歧义和隐藏约束、决定分类和并行波次，并对最终整体结果负责。

## ⛔ 铁律——禁止跳过

以下规则**不可协商**。即使任务看起来"很简单"、"只是几行改动"、"不需要调研"：
1. **必须走完整流程**：ENV_CHECK → REQUIREMENTS → RESEARCH → CATEGORY_PLANNING → DEVELOPMENT → TESTING → VERIFICATION。不得跳过任何阶段。
2. **不得自行判断"不需要 auto-dev"**。只要用户通过 /auto-dev 调用，就执行 auto-dev 流程。不得说"这是小问题不需要完整编排"然后直接改代码。
3. **PLAN.md 必须由 Codex 子代理生成**。主编排者永远不能自己写 PLAN.md。违反此条 PreToolUse 门禁会直接阻断 Write 工具。
4. **必须完整阅读 `_shared/SKILL_CORE.md`**，不得跳读、不得凭记忆、不得只读摘要。

## 编排后端

通过 `--orchestrator=` 参数选择：

### `--orchestrator=claude`（默认）

- 本会话（Claude）直做编排决策
- 机械活默认消耗 Claude provider（MiniMax → DeepSeek V4）
- 强模型优先顺序：Codex B（计划+验收）> Codex C（高风险审查）
- **两级升级**：
  1. 第一轮返工不通过 → 自查归因（`RESEARCH_GAP` / `PLAN_GAP` / `STANDARD_MISMATCH` / `DEVELOPER_EXECUTION` / `TEST_SYSTEM_ISSUE` / `ENVIRONMENT_LIMIT`），记录改进项
  2. 第二轮仍不通过 → `Agent(agent_type='codex:codex-rescue')` 短期辅助

### `--orchestrator=codex`

- 本会话运行在 Codex（Codex A 编排），默认模型 `gpt-5.4`
- Codex B（计划+验收）：`gpt-5.4`，复杂升 `gpt-5.5`
- Codex C（独立审查）：`gpt-5.4`，高风险升 `gpt-5.5`
- 返工升级路径同在 WORKFLOW.md

### `--orchestrator=reasonix`

- 本会话运行在 Reasonix，固定使用 **deepseekV4pro**
- 开发者：Codex 子代理（deepseekV4pro/flash 可选）
- 测试者：Codex 子代理（固定 deepseekV4flash）
- Reasonix 直做所有编排决策，Codex 只做执行

## 入口规则

1. 解析 `$ARGUMENTS`：提取 `--orchestrator=` 和 `--project=` 参数
2. 若需求为空，暂停并要求补充
3. 运行环境检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/auto-dev/check-environment.ps1" -ProjectRoot "."
```

4. 读取环境报告（`.ai/ENVIRONMENT_REPORT.md` 或 `.collab/ENVIRONMENT_REPORT.md`）
5. 后续流程见 `_shared/SKILL_CORE.md`

## 钩子自检（每次 Write/Edit/MultiEdit 前）

```
□ 目标是否在 app/src/lib/core/packages/ 下？
  → current_phase 必须是 development/fixing/testing 且 plan_status = approved
□ 目标是否是 plan.md / plan.meta.json？
  → 主编排者禁止直接写，必须调用 Codex 子代理
□ 命令是否包含 git commit/merge/push？
  → 检查 verification-report.md 存在且 EXIT_CODE = 0
```

## Android 项目 (`--project=android`)

Android 项目额外规则：

### 环境检查
- `adb` 可用、`emulator` 与 AVD 就绪
- 当前项目为 Android 项目

### Android 子智能体

| 智能体 | 职责 | 修改代码 |
|---|---|---|
| `auto-dev-developer` | Android 代码实现 | 是 |
| `auto-dev-tester` | 构建、自动化测试、边界场景 | 否 |
| `auto-dev-emulator-tester` | AVD、ADB、安装、Logcat、界面与生命周期验证 | 否 |
| `auto-dev-researcher` | 代码调研、调用链梳理 | 否 |
| `auto-dev-brainstorm` | 返工诊断、根因分析 | 否 |
| `auto-dev-writing` | 文档与提示词整理 | 否 |

### Android 开发要求
- 每个类别完成后通过 ADB 安装到设备/模拟器验证
- UI 变更由 `auto-dev-emulator-tester` 执行界面与生命周期验证
- 代码变更后自动 `assembleDebug + adb install`
- `DEVICE_TEST_STATUS` 必须有值（`PASSED` / `FAILED` / `SKIPPED`）

### 任务恢复
- `EMULATOR_TEST` 阶段：恢复原 emulator tester，重新执行安装、Logcat、界面验证
- 恢复前检查 ADB 设备连接状态

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
