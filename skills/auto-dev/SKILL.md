---
name: auto-dev
description: 通用批量开发入口。支持 Claude / Codex / OpenCode 三种编排后端，通过 --orchestrator= 参数切换。用于把一组需求或 Bug 组织成澄清、调研、分类、计划、受控并行开发、测试、验收与总回归。OpenCode + oh-my-openagent 场景下，本 Skill 作为项目级规则源，可下沉到 AGENTS.md / .omo/rules/**。
argument-hint: "<需求、Bug 现象与预期结果> [--orchestrator=claude|codex|opencode] [--project=android]"
disable-model-invocation: true
allowed-tools: Read Write Edit Glob Grep Bash Agent SendMessage
---

# Auto Dev

## ⛔ 第一步 —— 必须先读共享核心（违反此条 = 流程错误）

**在回复用户之前**，立即用 Read 工具完整读取以下 4 个文件。不读完、不展示关键规则摘要，**禁止**进入任何阶段：

| # | 文件 | 内容 |
|---|---|---|
| 1 | `../_shared/SKILL_CORE.md` | 核心规则、阶段路由、状态文件 schema、主编排角色 |
| 2 | `../_shared/WORKFLOW.md` | 状态机、角色模型、生产线、并行策略、返工闭环 |
| 3 | `../_shared/HOOKS.md` | 强制门禁清单、Gate 1-5、Claude Code hooks 配置 |
| 4 | `../_shared/MODEL_ROUTING.md` | 默认模型分工、强制规则、审查分轮、生产线规则 |

> 本文件只是**入口 + 差异化规则**（编排后端、类别分组、工作树 commit 规范、Android 路由）。
> 完整流程、状态机、门禁、模型路由全部定义在上述 4 个共享文件中。
> **跳读共享文件直接执行 = 必然出错 = 返工。**

> **STATE_DIR**：`.ai-work`（Claude / 通用默认）/ `.collab-work`（Codex 兼容模式）/ `.omo/auto-dev-work`（OpenCode + oh-my-openagent 可选桥接目录）
>
> PreToolUse guard：`../_shared/scripts/auto_dev_guard.py`

用户需求：

$ARGUMENTS

你是当前会话的**主编排者**。你不是纯调度器；你负责理解真实目标、结合代码判断需求、发现歧义和隐藏约束、决定分类和并行波次，并对最终整体结果负责。

## ⛔ 铁律——禁止跳过

以下规则**不可协商**。即使任务看起来"很简单"、"只是几行改动"、"不需要调研"：
0. **责任身份不共享对话，只复用同一责任身份的原会话**。Planner 与 plan reviewer 是不同责任身份，不是同一个人/会话：默认 planner 由 DeepSeek V4 Pro 承担，plan reviewer 通常由 Codex/GPT 承担。Plan reviewer 只提审查意见；planner 拥有 PLAN 的最终裁决与修订权。不同责任身份默认不同会话/子会话/CLI run；不得在同一个对话里先写计划又审自己的计划，或先开发又审自己的代码。复用规则是：谁开发谁返工，谁发现谁复验关闭；reviewer/tester 发现的问题必须回到对应 owner 处理：计划问题回 planner 修订 PLAN，代码问题回 developer 返工，原发现者复验关闭。跨身份只通过 `PLAN.md`、`PLAN_REVIEW.md`、`PLAN_REVIEW_RESOLUTION.md`、`HANDOFF.md`、`TEST_REPORT.md`、commit 交接。
0.1. **每个责任身份的原始输出必须保留，禁止覆盖**。Planner、plan reviewer、developer、tester、code reviewer、rescue 的原始产物都必须落盘保留，后续只能新增 `v2`、`round2`、`patch`、`resolution` 或 `superseded` 说明，不能直接覆盖上一轮原文。推荐命名：`PLAN.v1.md`、`PLAN_REVIEW.round1.gpt-5.4.md`、`PLAN_REVIEW_RESOLUTION.round1.md`、`PLAN_PATCH.v2.md`、`CODE_REVIEW.round1.gpt-5.4.md`、`CODE_REVIEW.round2.gpt-5.5.md`。`PLAN.md` / `PLAN_REVIEW.md` 可以作为当前入口或摘要，但必须能追溯到原始版本文件。
1. **必须走完整流程**：ENV_CHECK → REQUIREMENTS → RESEARCH → CATEGORY_PLANNING → DEVELOPMENT → TESTING → VERIFICATION。不得跳过任何阶段。
2. **不得自行判断"不需要 auto-dev"**。只要用户通过 /auto-dev 调用，就执行 auto-dev 流程。不得说"这是小问题不需要完整编排"然后直接改代码。
3. **PLAN.md 必须由计划代理生成，并且必须经过二次计划审查**。默认计划代理是 DeepSeek V4 Pro；OpenCode + oh-my-openagent 场景可用 `hyperplan` / 专用 plan wrapper 承载。主编排者永远不能自己写正式 `PLAN.md`，只能写 `plan-input.md`、边界条件和审查意见。
4. **必须完整阅读 `../_shared/SKILL_CORE.md`**，不得跳读、不得凭记忆、不得只读摘要。
5. **用户中途补充信息 ≠ 退出 auto-dev**。即使用户插话补充需求、提问或纠正，auto-dev 流程不会取消。收到任何消息后，第一步永远是读取 STATE.json 恢复状态，吸收用户补充，从当前阶段继续推进。不得因为用户插话就退化到普通聊天模式。
6. **分类由主编排者亲自做，计划每类独立出**。CATEGORY_DISCOVERY 是编排决策，严禁委托计划代理。BATCH_PLAN_BY_SUBAGENT = 每类一个独立计划代理调用（默认 DeepSeek V4 Pro planner，OpenCode/OMO 可用 hyperplan），严禁一个代理包揽所有类别。
7. **用户反馈 bug/问题/没改好 ≠ 直接改代码**。即使用户说"这个没改好"、"XX 还是不行"、"这里还有问题"、"闪退"、"UI 不对"，也**必须**先写 `plan-input.md` 或 `PLAN_PATCH.md` 描述问题根因和修改方案，然后交 DeepSeek V4 Pro planner 审查或生成修订计划。主编排者**禁止**直接根据用户反馈动手改代码——即使用户描述的修改"看起来很简单"、"只是改一行"、"只是加个判断"、"不需要调研"。必须先产出书面方案 → planner 审查批准 → 再改代码。这条没有例外。
8. **子代理派遣必须显式声明角色+模型**。每次用 Agent 工具 dispatch 子代理，**label 必须**用 `[角色:模型] 任务描述` 格式（见 `../_shared/SKILL_CORE.md` §5.2）。禁止省略模型名。主编排者自身**不是** planner、**不是** developer、**不是** reviewer——这些角色必须通过 Agent 工具派遣对应模型的子代理执行。

## 会话恢复协议 —— 每轮对话第一步，不可跳过

无论用户发来什么消息——补充需求、提问、纠正、甚至闲聊——在回复之前必须先执行：

1. **读取 `{STATE_DIR}/STATE.json`**
2. 根据 `current_phase` 和消息类型判断处理：

   | `current_phase` | 收到的消息 | 处理 |
   |---|---|---|
   | `done` | 纯文字（"我想说的是 X"） | 正常聊天回复 |
   | `done` | `/auto-dev` 或 `/auto-code-android-dev` 触发 | **新任务**：从 ENV_CHECK 开始 |
   | `blocked` | 任何消息 | **必须询问用户**："上一任务仍在 blocked 状态。是先收尾，还是开始新任务？" |
   | 其它（非 done/blocked） | **用户反馈 bug/问题/没改好** | ⛔ **禁止直接改代码**。回退到 `planning` 阶段，写 `plan-input.md` / `PLAN_PATCH.md`，交 DeepSeek V4 Pro planner 审查，批准后再进入 `development` |
   | 其它（intake/research/planning/development/testing/acceptance/fixing/integration/verification） | 纯文字补充（非 bug 反馈） | **流程内补充输入**：将消息融入当前阶段，**不得**重新开始、**不得**退回 |
   | 其它（非 done/blocked） | `/auto-dev` 或 `/auto-code-android-dev` 触发 | **必须询问用户**："上一任务在 X 阶段尚未完成。是先收尾，还是开始新任务？" |

3. 若 STATE.json 不存在：这是首次调用，从 ENV_CHECK 开始
4. **不得自行判断**任务结束或开始新任务。遇到非 done 状态收到 /skill 调用时，**必须**先询问用户
5. **向用户报告**：当前阶段 + 下一步动作，确认后执行

### 用户插话处理规则

| 用户消息类型 | 处理方式 |
|---|---|
| **反馈 bug/问题/没改好/闪退/UI不对** | ⛔ **禁止直接改代码**。① 写 `plan-input.md` 或 `PLAN_PATCH.md` 描述问题根因 + 修改方案；② 交 DeepSeek V4 Pro planner 审查或生成修订计划；③ planner 批准后才允许改代码。**即使"只改一行"也不得跳过** |
| 补充需求/约束 | 融入 REQUIREMENTS.md，评估是否需要重新分类。若涉及已实现代码的修改，按上条"反馈 bug"处理 |
| 纠正错误理解 | 更新 DECISIONS.md，检查是否影响已完成阶段。若需要改代码，按"反馈 bug"处理——先写方案再审查 |
| 提问当前进度 | 报告 STATE.json 摘要 + 当前阶段产物清单，不中断流程 |
| 要求跳过/加速 | 评估风险后决定，但不得跳过强制门禁（plan_must_be_agent、pre_commit_gate 等） |
| **带 /skill 触发且任务未 done** | **必须询问用户**：先收尾当前任务还是开始新任务 |
| 无关闲聊 | 一句话回复后立即回到流程，不展开新话题 |

### `blocked` 状态处理

`current_phase = blocked` 表示任务暂停等待外部条件。主编排 **不得自行 unblock**。

进入条件（参考 `../_shared/SKILL_CORE.md` §2.1）：
- 用户主动说"先暂停/先做别的"
- 关键依赖不可用（DeepSeek V4 Pro 计划入口不可用，且主编排被禁止直接写 PLAN）
- 外部/人工验收中用户挂断/出门
- 同一类别编译/测试反复失败 ≥ 3 次
- 关键外部 API 不可用
- Plan Agent 反复 PLAN_GAP 2 次以上

进入 blocked 时：
1. STATE.json 加 `block_reason` 字段
2. 写 `.ai-work/runs/<task>/BLOCKED.md` 记录原因
3. 报告用户："任务已 block, 原因: X, 解除需要: Y, 等你确认"

解除 blocked：
- 仅用户明确指令"恢复/继续/解除" 时执行
- 删除 block_reason
- 回到 blocked 前的阶段
- 在 BLOCKED.md 记录解除时间和原因

## 编排后端

通过 `--orchestrator=` 参数选择：

### `--orchestrator=claude`（默认）

- 本会话（Claude）直做编排决策：需求理解、Research 事实判断、类别划分、wave 调度、返工归因、最终完成判断。
- 默认模型路由：Claude Code 作为壳，MiniMax M3 承担日常主编排；DeepSeek V4 Pro 负责每类计划；Codex/GPT 负责二次计划审查和关键代码审查：第一轮审查用 GPT-5.4，第二轮复审/升级审查用 GPT-5.5。MiniMax M3 负责开发和测试。GPT/Codex 无额度时记录延期（仅审计追溯，不自动补跑），不阻塞 DeepSeek 计划 + MiniMax 开发/测试。
- 若 OpenCode + oh-my-openagent 已经固定启用，不要重复造一套后台团队；把本 Skill 的核心规则写入 `AGENTS.md` / `.omo/rules/auto-dev.md`，让 OMO 的 rules injection 自动加载。
- 两级升级：
  1. 第一轮返工不通过 → 自查归因（`RESEARCH_GAP` / `PLAN_GAP` / `STANDARD_MISMATCH` / `DEVELOPER_EXECUTION` / `TEST_SYSTEM_ISSUE` / `ENVIRONMENT_LIMIT`），记录改进项。
  2. 第二轮仍不通过 → 优先回到同类别生产线做返工归因；若 Codex 有额度，可调用 Codex 做计划复核、关键代码审查或救火。Codex 无额度时记录 `CODEX_STATUS.json` 与 `DEFERRED_CODEX_REVIEW.md`，不阻塞默认流程。

### `--orchestrator=codex`

- 本会话运行在 Codex / GPT 类高能力模型时，Codex 不再默认承担所有计划。
- 推荐定位：高风险计划复核、关键代码审查、复杂 bug 二次判断、最终兜底。
- 若 GPT 额度不足，不设置 GPT 审查环节；Codex 额度也不足时，记录延期审查并继续，不让流程进入 blocked。
- Codex Light / LazyCodex 可提供 rules、comment-checker、git-bash、LSP、ultrawork、ulw-loop 等便携组件；但 Codex CLI 自身负责 agent surface，不使用 OMO Ultimate 的 `team_*` 工具。

### `--orchestrator=opencode`

- 本会话运行在 OpenCode，推荐固定启用 oh-my-openagent Ultimate。
- 本 Skill 不再试图替代 OMO 的 Sisyphus / Team Mode；本 Skill 只负责定义**项目级流程约束**：Research First、主编排分类、每类独立计划、受控并行、测试先行、同类生产线串行、工作树卫生、验证闭环。
- 推荐映射：

| 本 Skill 角色 | OpenCode / OMO 对应能力 | 使用方式 |
|---|---|---|
| 主编排者 | Lead / Sisyphus | 负责意图理解、分类、wave、返工路由 |
| 计划代理 | `hyperplan` 或 plan wrapper | 对每个类别生成 / 审查 `PLAN.md` |
| 开发者 | deep / Hephaestus / team member | 只处理分配类别，不跨类别乱改 |
| 测试者 | reviewer / tester / team member | 只验证，不默认改生产代码 |
| 调研代理 | search / analyze / LSP / grep_app / codegraph | 产出 `CODE_CONTEXT.md`，事实标注 CONFIRMED/INFERRED/UNKNOWN |

- OpenCode + OMO 场景下，优先把规则放到：
  - 项目根 `AGENTS.md`
  - `.omo/rules/auto-dev.md`
  - `.opencode/oh-my-openagent.jsonc`（只放 team/concurrency 配置，不塞长流程）

## 模型路由与二次计划审查

### 默认路由

| 角色 | 默认模型 / 工具 | 说明 |
|---|---|---|
| 日常主编排 | Claude Code 壳 + MiniMax M3 | 负责状态恢复、需求理解、类别划分、wave 调度、返工归因。 |
| 计划代理 | DeepSeek V4 Pro | 每个类别独立生成 `PLAN.md` + `plan.meta.json`。 |
| 二次计划审查 | Codex/GPT-5.4（第一轮；同任务可 resume，跨框架用文件交接） | `PLAN.md` 生成后优先调用；无额度时记录延期审查，不阻塞开发。 |
| 第二轮复审 / 升级审查 | GPT-5.5（有额度时） | 当第一轮 review 要求修改、planner 修订后复审，或同类多轮返工仍不收敛时调用；无额度则记录延期，不设置替代 GPT 环节。 |
| 开发代理 | MiniMax M3 | 按已批准 PLAN 执行实现、自测、原子 commit。 |
| 测试代理 | MiniMax M3 | 构建、测试、验收、复验，不默认改生产代码。 |
| 更高风险增强 | GPT（有额度时） | 在 Codex 之外做架构级判断、最终兜底、复杂 bug 二次判断。 |

Codex/GPT 是**二次计划审查与关键代码审查的首选代理**，但受额度限制。第一轮计划/代码审查用 GPT-5.4；第二轮复审、返工后复审、升级审查**必须**用 GPT-5.5（有额度时），**禁止**退回到 GPT-5.4。理由：GPT-5.4 已审过第一轮且没拦住问题，返工后再用 GPT-5.4 等于浪费额度。无额度时不让任务 blocked，而是记录 `CODEX_STATUS.json` / `GPT_REVIEW_STATUS.json` 与 `DEFERRED_CODEX_REVIEW.md`（仅审计追溯），当前任务继续推进。

### 二次计划审查（强制）

每个类别的 `PLAN.md` 生成后，必须进入 `plan_review`，不得直接进入 `development`。

二次计划审查要求：

1. `PLAN.md` 由 DeepSeek V4 Pro planner 生成；第一轮 `PLAN_REVIEW` 由 Codex/GPT-5.4 审查生成；若 planner 根据审查意见修订后需要第二轮复审，**必须**用 GPT-5.5（有额度时）。计划作者和审查者不能是同一责任身份。Codex/GPT CLI 只能复用自己对应的会话 / resume；跨 Claude/Codex/OpenCode 时通过文件交接。无额度时写入延期审查记录，不强制等待。
2. 审查输出 `PLAN_REVIEW.md` + `plan-review.meta.json`，至少包含：
   - `PLAN_REVIEW_STATUS: approved | changes_required | blocked`
   - 需求覆盖检查
   - 文件范围检查
   - 测试先行检查
   - 风险与回滚检查
   - 跨类别接口 / 状态机冲突检查
3. 只有当 `plan_status = approved` 且 `plan_review_status = approved` 时，才能正常进入开发；若 Codex/GPT 无额度，必须记录 `DEFERRED_CODEX_REVIEW.md` 并把 `plan_review_status` 标为 `deferred_due_to_quota` 或 `deferred_due_to_codex_quota` 后才允许继续。
4. 计划审查阶段多花一次模型调用，优先于开发后返工；不要为了省一次 review 让 MiniMax 执行错误计划。

#### 计划审查回传与 Planner 裁决

`PLAN_REVIEW.md` 不是最终改计划的人，它是 Codex plan reviewer 给出的二次审查意见。审查结束后必须回传给原 planner / 计划 owner（默认 DeepSeek V4 Pro planner）：

1. `PLAN_REVIEW_STATUS = approved`：planner 确认无须修订，主编排记录批准，进入 `TEST_TARGET`。
2. `PLAN_REVIEW_STATUS = changes_required`：planner 必须逐条判断 Codex 审查意见是否成立，输出 `PLAN_REVIEW_RESOLUTION.md`；成立的意见必须修订 `PLAN.md` 或写 `PLAN_PATCH.md`，不成立的意见必须写明证据和理由。
3. 修订后的 PLAN/PLAN_PATCH 必须回到审查链复审：第一轮问题修订后**必须**用 GPT-5.5 做第二轮复审（有额度时），**禁止**用 GPT-5.4 重复审；如果 GPT/Codex 无额度，则记录延期复审，但不能静默忽略已提出的 blocker。
4. planner / plan reviewer 都属于开发前的计划把关链，但不是同一责任身份：Codex reviewer 负责挑错，DeepSeek V4 Pro planner 负责裁决和改计划；二者都不直接进入开发实现。

只有 `PLAN_REVIEW` 的问题被 planner 裁决并处理后，才能进入 `TEST_TARGET`。

### 会话复用边界（Claude / Codex / OpenCode）

"同类别复用"分两层：

1. **文件化上下文必定复用**：同一类别始终复用 `PLAN.md`、`PLAN_REVIEW.md`、`HANDOFF.md`、`FOLLOWUP-<n>.md`、commit 和测试报告。
2. **工具会话尽量复用，但不跨框架强求**：
   - Claude 框架内的 MiniMax / DeepSeek V4 Pro 流程，也不能在同一对话里随意切换责任身份。planner、reviewer、developer、tester 应使用不同 Claude 子会话/任务上下文；只有同一责任身份的返工或复验才优先回原会话继续。
   - Codex CLI 的计划/审查/救火，只能复用同一个 Codex 会话或 resume 入口；不能和 Claude/OpenCode 共享聊天上下文。
   - OpenCode + OMO 的 `hyperplan` / `ultrawork`，只能复用 OpenCode/OMO 自己的会话、team run 或任务目录；不能和 Claude/Codex 共享聊天上下文。

因此，**当前同一回合的 PLAN 和 PLAN_REVIEW 即使都在 Claude 框架内，也不应由同一责任会话自写自审；不同框架更不叫复用同一会话，只叫复用同一类别文件化上下文**。用户反馈后的二次计划修订、返工、救火，若仍属同类别/同模块，按责任身份回到原会话继续：原 developer 修，原 reviewer/tester 复验关闭。

### Plan Agent 自动选择

按下列顺序尝试计划 / 审查入口：

```text
1. DeepSeek V4 Pro planner 可用吗？
   └─ YES → 通过 OpenCode/OMO hyperplan、run-opencode-plan、run-deepseek-plan 或项目包装层生成每类 PLAN.md

2. Codex/GPT plan reviewer 有额度吗？
   └─ YES → 第一轮用 GPT-5.4 读取 PLAN.md，输出 PLAN_REVIEW.round1.gpt-5.4.md；若 changes_required，回传 planner 裁决并修订 PLAN/PLAN_PATCH，再用 GPT-5.5 做第二轮复审
   └─ NO / usage limit → 写 CODEX_STATUS.json / GPT_REVIEW_STATUS.json + DEFERRED_CODEX_REVIEW.md，plan_review_status = deferred_due_to_quota，不阻塞默认流程

3. GPT 有额度且当前节点需要更高风险增强吗？
   └─ PLAN_REVIEW 节点 YES → 可额外调用 GPT 做架构级计划复核；审查结果写入 `GPT_PLAN_REVIEW.md` 或附加到 `PLAN_REVIEW.md`
   └─ CODE_REVIEW 节点 YES → 可额外调用 Codex 审关键 diff / 高风险代码；结果写入 `CODEX_CODE_REVIEW.md`
   └─ RESCUE 节点 YES → 可额外调用 Codex 做复杂 bug 二次判断或救火
   └─ NO / usage limit → 跳过 Codex/GPT 增强；Codex usage limit 时记录 `CODEX_STATUS.json` 与 `DEFERRED_CODEX_REVIEW.md`，不阻塞默认流程

4. DeepSeek V4 Pro 计划入口不可用：
   current_phase = blocked
   block_reason = "NO_PLAN_OR_REVIEW_AGENT_AVAILABLE"
   禁止主编排者直接写正式 PLAN.md 或直接放行开发
```

### 决策日志

每次选择记录到 `{STATE_DIR}/runs/<task>/PLAN_DECISION.json`：

```json
{
  "task_id": "...",
  "timestamp": "...",
  "planner": {"model": "deepseek-v4-pro", "available": true, "entry": "opencode-omo-hyperplan"},
  "plan_reviewer": {"model": "codex", "available": true, "entry": "codex-plan-review"},
  "codex_enhancement": {
    "attempted": true,
    "available": false,
    "reason": "usage_limit",
    "reset_at": "2026-07-09T20:07:00+09:00",
    "deferred_file": ".ai-work/runs/.../DEFERRED_CODEX_REVIEW.md"
  },
  "plan_file": ".ai-work/runs/.../category-a/PLAN.md",
  "plan_review_file": ".ai-work/runs/.../category-a/PLAN_REVIEW.md"
}
```

### Codex 额度不足处理

Codex 只作为增强项；失败不等于流程失败。

- PLAN_REVIEW 节点 Codex 无额度：记录延期，`plan_review_status = deferred_due_to_codex_quota`，不阻塞当前开发。延期仅审计追溯，不自动补跑。
- CODE_REVIEW 节点 Codex 无额度：记录待补代码审查，继续使用默认代码审查与测试证据推进。
- RESCUE 节点 Codex 无额度：不重复盲试，记录延期救火项，交由主编排做归因；必要时让 DeepSeek V4 Pro 重新修订计划。
- 记录位置：`{STATE_DIR}/CODEX_STATUS.json` 和 `{STATE_DIR}/runs/<task-id>/DEFERRED_CODEX_REVIEW.md`。
- 延期记录仅用于审计追溯。任务已通过 MiniMax 开发/测试完成交付，不自动补跑。

### Plan Agent 拒绝 / PLAN_GAP 处理

- 第一次 `PLAN_GAP`：主编排者补充 `plan-input.md`，明确需求、文件范围、不可改区域和验收命令，再重跑同一个计划代理。
- 第二次 `PLAN_GAP`：优先在同类别生产线内修改 `PLAN.md` 后再次调用 Codex 审查；Codex 无额度则记录延期（仅审计追溯）。
- 第三次仍失败：进入 `blocked`，原因写 `PLAN_AGENT_REPEATED_PLAN_GAP`，需要用户补充需求或允许缩小范围。

## 入口规则

1. 解析 `$ARGUMENTS`：提取 `--orchestrator=` 和 `--project=` 参数
2. 若需求为空，暂停并要求补充
3. 运行环境检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<project wrapper script>" -ProjectRoot "."
```

其中：
- 通用项目可提供 `scripts/auto-dev/check-environment.ps1`
- 若参数包含 `--project=android`，或环境检查确认当前是 Android 项目，应切换/转交 `auto-code-android-dev` 包装层；Android 环境检查脚本与设备验证规则只在该包装层定义

4. 读取环境报告（`.ai/ENVIRONMENT_REPORT.md` 或 `.collab/ENVIRONMENT_REPORT.md`）
5. 后续流程见 `../_shared/SKILL_CORE.md`

## 钩子自检（每次 Write/Edit/Bash/Agent 前）

```
□ 目标是否在 app/src/lib/core/packages/ 下？
  → current_phase 必须是 development/fixing/testing 且 plan_status = approved
□ 目标是否是 plan.md / plan.meta.json？
  → 主编排者禁止直接写，必须 dispatch [planner:deepseek-v4-pro]
□ 是否准备进入 development/fixing/testing？
  → plan_status 和 plan_review_status 都必须是 approved
□ 命令是否包含 git merge/push/release/done？
  → 检查 verification-report.md 存在且 EXIT_CODE = 0
□ 是否在 Agent dispatch？
  → label 必须用 [角色:模型] 格式
□ 是否在 Bash 调用 Codex？
  → 必须先报告: 「Codex 调用: [用途, 模型:gpt-5.x, 输入, 预期输出]」
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

## Android 项目路由（职责边界）

`auto-dev` 只定义通用开发流程，不承载 Android 细节。

当出现以下任一情况时，主编排者应转入 `auto-code-android-dev` 包装层继续：

- 用户显式调用 `/auto-code-android-dev`
- `$ARGUMENTS` 包含 `--project=android`
- 环境检查确认当前项目是 Android / Gradle / APK 项目
- 任务需要 ADB、模拟器、真机、APK 安装、Logcat、Android 生命周期、权限、后台服务等 Android 专用验证

转交后仍继承本文件的通用规则：Research First、主编排亲自分类、每类独立计划、二次计划审查、同类生产线串行、不同类受控并行、测试先行、工作树卫生和完成前验证。

Android 专用命令、设备门禁、用户真机实测和 `DEVICE_TEST_STATUS` 等细节只在 `auto-code-android-dev/SKILL.md` 中定义；本通用入口不重复描述，避免两套规则打架。

## 共享文件引用

- `../_shared/SKILL_CORE.md` — 核心规则 + 钩子
- `../_shared/HOOKS.md` — 完整门禁定义
- `../_shared/WORKFLOW.md` — 状态机 + 角色模型
- `../_shared/ROUTING.md` — 所有者路由
- `../_shared/MODEL_ROUTING.md` — 模型路由（默认分工 + 强制规则）
- `../_shared/REPORT_FORMATS.md` — 报告模板
- `../_shared/WORKTREE_GUIDE.md` — worktree 布局
- `../_shared/SKILL_VERSIONING.md` — 版本管理规范
- `../_shared/skills/*.md` — 8 个子阶段 skill
- `../_shared/templates/*.md` — 模板
- `../_shared/scripts/auto_dev_guard.py` — PreToolUse guard

## 类别分组与并发/串行决策

**CATEGORY_PLANNING 阶段的核心决策**：哪些需求在同一类别（强耦合），哪些在独立类别（可并发）。

### 类别分组规则

| 需求关系 | 分组 | 计划 | 执行 |
|---|---|---|---|
| **同文件 / 同模块 / 强耦合** | 同一类别 | 一次 PLAN.md + 一次 PLAN_REVIEW.md | 一条生产线串行 |
| **不同文件 / 无依赖** | 不同类别 | 各自 PLAN.md + PLAN_REVIEW.md | 多条生产线并发（各自 worktree） |
| **A 输出是 B 输入** | 跨类别但有依赖 | 各自 PLAN.md + PLAN_REVIEW.md | 生产线串行：A 完成再启动 B |

### 决策算法

```
对每个需求对 (req_i, req_j):
  if 同文件 或 同一数据流/状态机:
    同类别
  elif B 依赖 A 的输出:
    跨类别, A → B 串行
  else:
    独立类别, 可并发
```

### 类别生产线顺序

同一类别内必须串行推进，不能把计划、开发、测试、代码审查拆成互相抢上下文的并发任务：

```text
CATEGORY_PLAN
-> CATEGORY_PLAN_REVIEW   ← 只审一次（首次 gpt-5.4 / 返工 gpt-5.5）
-> CATEGORY_TEST_TARGET
-> IMPLEMENT_LOOP
-> CATEGORY_TEST
-> CATEGORY_CODE_REVIEW
-> CATEGORY_ACCEPTANCE
-> FOLLOWUP/REPAIR
```

- 计划审查、代码审查和多次救火默认复用当前类别的文件化上下文；会话复用只发生在同一责任身份内：原 developer 负责返工，原 reviewer/tester 负责复验关闭。跨身份、跨 Claude/Codex/OpenCode 时只通过文件交接。
- 不同类别才允许并行；同一类别的各工位是一条有始有终的生产线。
- 测试先行落在 `CATEGORY_TEST_TARGET` 与 `IMPLEMENT_LOOP` 之间：先写失败测试/最小复现/可执行验收脚本，再写实现。

### Agent 协调（主编排职责）

并发流水线中，**决策协调经主编排**；但子代理之间允许传递文件路径、commit hash 和简短状态，避免主编排搬运全文：

| 场景 | 处理 |
|---|---|
| Agent 报完成 | 主编排决定是否启动依赖项 / wave 合并 |
| Agent 报异常 | 主编排先路由给原责任会话；必要时再派 brainstorm/审查代理诊断 |
| Agent 报 "需要 X 才能继续" | 主编排决定：等其它流水线 / 调整 plan / 询问用户 |
| 同模块追加问题 | 原开发/测试会话继续，写 `FOLLOWUP-<n>.md`，不从零重跑完整 plan |
| 多 Agent 写同一文件 | 主编排 merge 冲突，**不要让 Agent 自行 resolve** |

### 流水线状态同步

每条并发流水线通过心跳机制与主编排同步：

```
[流水线 A]  ───heartbeat───>  [主编排]
                                  │
[流水线 B]  ───heartbeat───>  [主编排]
                                  │
[流水线 C]  ───heartbeat───>  [主编排]
```

- 主编排**唯一**决定：wave 边界、合并时机、阻塞处理
- Agent 心跳包括：当前步骤、commit hash、未完成项、异常

### 同会话优先与同模块追加问题

- 同一类别、同一模块、同一状态机链路，优先恢复原开发/测试会话继续处理。
- 用户反馈后的二次计划修订、代码审查和多次救火，若仍属同类别/同模块，优先回到原责任会话继续：原 planner 接收 Codex 审查意见，裁决并修订 PLAN/PLAN_PATCH，原 developer 修代码，原 reviewer/tester 复验关闭；但当前回合 PLAN 与 PLAN_REVIEW 不能由同一责任会话自审，跨框架时只能用文件交接。只有用户开启下一批需求、显式结束上个对话、上下文污染或多轮同错时才切新会话。
- 用户在验收或人工实测时反馈的同模块新问题，先追加到原类别：`ISSUES.json` + `FOLLOWUP-<n>.md`。
- 若追加问题仍在原 PLAN 边界内，只写 `PLAN_PATCH.md` 并做定点审查；不要回到首次 plan 会话从零跑。
- 只有跨模块、跨公共接口、影响基础状态机或改变验收标准时，才重新进入 CATEGORY_DISCOVERY。
