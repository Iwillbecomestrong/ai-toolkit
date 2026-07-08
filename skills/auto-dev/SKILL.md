---
name: auto-dev
description: 通用批量开发入口。支持 Claude / Codex / Reasonix 三种编排后端，通过 --orchestrator= 参数切换。用于把一组需求或 Bug 组织成澄清、调研、分类、计划、受控并行开发、测试、验收与总回归。仅在用户明确运行 /auto-dev 并提供需求时使用。
argument-hint: "<需求、Bug 现象与预期结果> [--orchestrator=claude|codex|reasonix] [--project=android]"
disable-model-invocation: true
allowed-tools: Read Write Edit Glob Grep Bash Agent SendMessage
---

# Auto Dev

> **共享核心**：通用规则、钩子、工作流、路由、报告格式见 `../_shared/SKILL_CORE.md`。
>
> **STATE_DIR**：`.ai-work`（通用）/ `.collab-work`（`--orchestrator=codex|reasonix` 默认时）
>
> **强制门禁**：见 `../_shared/HOOKS.md`。PreToolUse guard：`../_shared/scripts/auto_dev_guard.py`
>
> **运行可观测性**：凡是启动 Codex plan/review/implement，都必须使用会写 `status.json`、stdout/stderr 日志、静默超时状态的包装脚本。不得黑箱等待。

用户需求：

$ARGUMENTS

你是当前会话的**主编排者**。你不是纯调度器；你负责理解真实目标、结合代码判断需求、发现歧义和隐藏约束、决定分类和并行波次，并对最终整体结果负责。

## ⛔ 铁律——禁止跳过

以下规则**不可协商**。即使任务看起来"很简单"、"只是几行改动"、"不需要调研"：
1. **必须走完整流程**：ENV_CHECK → REQUIREMENTS → RESEARCH → CATEGORY_PLANNING → DEVELOPMENT → TESTING → VERIFICATION。不得跳过任何阶段。
2. **不得自行判断"不需要 auto-dev"**。只要用户通过 /auto-dev 调用，就执行 auto-dev 流程。不得说"这是小问题不需要完整编排"然后直接改代码。
3. **PLAN.md 必须由 Codex 子代理生成**。主编排者永远不能自己写 PLAN.md。违反此条 PreToolUse 门禁会直接阻断 Write 工具。
4. **必须完整阅读 `../_shared/SKILL_CORE.md`**，不得跳读、不得凭记忆、不得只读摘要。
5. **用户中途补充信息 ≠ 退出 auto-dev**。即使用户插话补充需求、提问或纠正，auto-dev 流程不会取消。收到任何消息后，第一步永远是读取 STATE.json 恢复状态，吸收用户补充，从当前阶段继续推进。不得因为用户插话就退化到普通聊天模式。
6. **分类由主编排者亲自做，计划每类独立出**。CATEGORY_DISCOVERY 是编排决策，严禁委托 Codex。BATCH_PLAN_BY_SUBAGENT = 每类一个独立 Codex planner（N 类 = N 次调用），严禁一个 Codex 包揽全部类别。

## 会话恢复协议 —— 每轮对话第一步，不可跳过

无论用户发来什么消息——补充需求、提问、纠正、甚至闲聊——在回复之前必须先执行：

1. **读取 `{STATE_DIR}/STATE.json`**
2. 根据 `current_phase` 和消息类型判断处理：

   | `current_phase` | 收到的消息 | 处理 |
   |---|---|---|
   | `done` | 纯文字（"我想说的是 X"） | 正常聊天回复 |
   | `done` | `/auto-dev` 或 `/auto-code-android-dev` 触发 | **新任务**：从 ENV_CHECK 开始 |
   | `blocked` | 任何消息 | **必须询问用户**："上一任务仍在 blocked 状态。是先收尾，还是开始新任务？" |
   | 其它（intake/research/planning/development/testing/acceptance/fixing/integration/verification） | 纯文字补充 | **流程内补充输入**：将消息融入当前阶段，**不得**重新开始、**不得**退回 |
   | 其它（非 done/blocked） | `/auto-dev` 或 `/auto-code-android-dev` 触发 | **必须询问用户**："上一任务在 X 阶段尚未完成。是先收尾，还是开始新任务？" |

3. 若 STATE.json 不存在：这是首次调用，从 ENV_CHECK 开始
4. **不得自行判断**任务结束或开始新任务。遇到非 done 状态收到 /skill 调用时，**必须**先询问用户
5. **向用户报告**：当前阶段 + 下一步动作，确认后执行

### 用户插话处理规则

| 用户消息类型 | 处理方式 |
|---|---|
| 补充需求/约束 | 融入 REQUIREMENTS.md，评估是否需要重新分类 |
| 纠正错误理解 | 更新 DECISIONS.md，检查是否影响已完成阶段 |
| 提问当前进度 | 报告 STATE.json 摘要 + 当前阶段产物清单，不中断流程 |
| 要求跳过/加速 | 评估风险后决定，但不得跳过强制门禁（plan_must_be_codex、pre_commit_gate 等） |
| **带 /skill 触发且任务未 done** | **必须询问用户**：先收尾当前任务还是开始新任务 |
| 无关闲聊 | 一句话回复后立即回到流程，不展开新话题 |

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
- 返工升级路径同在 `../_shared/WORKFLOW.md`

### `--orchestrator=reasonix`

- 本会话运行在 Reasonix，固定使用 **deepseekV4pro**
- 开发者：Codex 子代理（deepseekV4pro/flash 可选）
- 测试者：Codex 子代理（固定 deepseekV4flash）
- Reasonix 直做所有编排决策，Codex 只做执行

## Plan Agent 自动选择 (Fallback 决策树)

按下列顺序尝试 plan agent，**任何一个能用就用，不行则跳过**：

```
1. Codex 可用吗?
   test:  echo "Say hi" | codex exec -C . --sandbox read-only --color never -m gpt-5.4 - 2>&1 | head -3
         检查输出是否包含 "ERROR: You've hit your usage limit"
   └─ YES → scripts/auto-code-android-dev/run-codex-plan.ps1 (前台, 等待 PLAN.md)
   
2. Reasonix 可用吗?
   test:  reasonix --version && echo $DEEPSEEK_API_KEY | head -c 5
   └─ OK → reasonix run -m deepseek-v4-pro --effort high --no-config
                "You are planner B, write PLAN.md to {path}"
            提示中禁止要求任何网页搜索/MCP 工具调用
            等待 Reasonix 写出 PLAN.md

3. 两者都不可用:
   主编排者直接写 PLAN.md, 顶部必须包含声明:
   "**PLAN 由主编排者直接编写 (Codex 限流 + Reasonix 不可用)**"
   用户明确 override 后可执行
```

### 决策日志

每次选择记录到 `.ai-work/runs/<task>/PLAN_DECISION.json`:
```json
{
  "task_id": "...",
  "timestamp": "...",
  "codex": {"tested": true, "available": false, "reason": "usage limit"},
  "reasonix": {"tested": true, "available": true, "model": "deepseek-v4-pro"},
  "fallback": "reasonix",
  "output": ".ai-work/runs/.../PLAN.md"
}
```

## 入口规则

1. 解析 `$ARGUMENTS`：提取 `--orchestrator=` 和 `--project=` 参数
2. 若需求为空，暂停并要求补充
3. 运行环境检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<project wrapper script>" -ProjectRoot "."
```

其中：
- 通用项目可提供 `scripts/auto-dev/check-environment.ps1`
- IronWill Android 包装层使用 `scripts/auto-code-android-dev/check-environment.ps1`

4. 读取环境报告（`.ai/ENVIRONMENT_REPORT.md` 或 `.collab/ENVIRONMENT_REPORT.md`）
5. 后续流程见 `../_shared/SKILL_CORE.md`

## 钩子自检（每次 Write/Edit/MultiEdit 前）

```
□ 目标是否在 app/src/lib/core/packages/ 下？
  → current_phase 必须是 development/fixing/testing 且 plan_status = approved
□ 目标是否是 plan.md / plan.meta.json？
  → 主编排者禁止直接写，必须调用 Codex 子代理
□ 命令是否包含 git commit/merge/push？
  → 检查 verification-report.md 存在且 EXIT_CODE = 0
```

## ⛔ 工作树 commit 规范（强约束）

为防止 Agent 在 working tree 累积未提交改动**导致 linter/编辑器/session 中断时全丢**（实测 100+ 行代码丢失事件），
**强制每完成一个原子步骤立即 commit**：

### `commit_step_gate`（每步强制）

1. 任何 Edit/Write/Bash 修改源码或文档后，**必须**在同一 Agent 的下一步操作前：
   ```bash
   git status --short   # 确认本次修改范围
   git add <精确文件>  # 不要用 git add . / git add -A
   git commit -m "<明确的 step message>"
   ```
2. 禁止"先把所有改完再一次性 commit"——这是工作树丢失的**主因**。
3. 禁止用 `git add .` / `git add -A`——会带进无关文件，必须精确指定。

### `working_tree_audit`（任务结束强制）

Agent 退出/任务完成/子任务切换前，**必须**：

```bash
# 1. 验证 working tree 干净
git status --short
# 输出必须为空，否则 commit 或 revert
# 如果有改动但属于当前任务, commit; 如果属于 pre-existing 改动, 通知用户决定
```

### 失败模式

- 任务结束 `git status` 不为空 → 不得声称"完成"
- Agent 报"已完成"但 `git log --oneline` 没有新 commit → 主编排必须强制重做或 commit
- 多个 Agent 并行时，每个 Agent 只 commit 自己负责的文件

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

- `../_shared/SKILL_CORE.md` — 核心规则 + 钩子
- `../_shared/HOOKS.md` — 完整门禁定义
- `../_shared/WORKFLOW.md` — 状态机 + 角色模型
- `../_shared/ROUTING.md` — 所有者路由
- `../_shared/REPORT_FORMATS.md` — 报告模板
- `../_shared/WORKTREE_GUIDE.md` — worktree 布局
- `../_shared/SKILL_VERSIONING.md` — 版本管理规范
- `../_shared/skills/*.md` — 8 个子阶段 skill
- `../_shared/templates/*.md` — 模板
- `../_shared/scripts/auto_dev_guard.py` — PreToolUse guard
