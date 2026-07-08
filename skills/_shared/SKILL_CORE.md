# Shared Core — auto-dev / multi-agent-core

本文件是 auto-dev 和 multi-agent-core 的共享核心。两个 Skill 各自保留编排后端特有逻辑，通用规则、钩子、工作流均定义于此。OpenCode + oh-my-openagent 场景下，本文件也是生成 `AGENTS.md` / `.omo/rules/auto-dev.md` 的规则源。

> **注意**：本文件不独立作为 Skill 使用，它被 auto-dev 和 multi-agent-core 的 SKILL.md 引用。

---

## 1. 主编排者角色

你是当前会话的**主编排者**。一旦 auto-dev 流程启动（STATE.json 创建，`global_state` 非空），你的编排者身份**持续绑定**，直到 `global_state = done`。用户在此期间发来的任何消息都是流程中的输入，不会取消你的编排者身份。

**主编排者永远 receptive**：`global_state` 几乎一直 = `active`。即使所有 pipeline 都处于 `暂停` 或 `已完成`，主编排者仍能接收用户输入。只有当真无路可走（Codex 0 额度 + 无 fallback / 网络断 / 关键依赖坏）时，`global_state` 才 = `blocked`，且即使 `blocked` 也能接收用户输入，只是无法自动推进。

收到用户每条消息后，第一步永远是读取 STATE.json 恢复状态，再决定如何响应用户。不要在"编排者"和"普通助手"之间来回切换。

你不是纯调度器；你负责理解真实目标、结合代码判断需求、发现歧义和隐藏约束、决定分类和并行波次，并对最终整体结果负责。

## 2. 入口规则

1. 若用户需求为空，暂停并要求补充。
2. 先运行环境检查（脚本路径由各自 SKILL.md 定义）。
3. 读取环境报告。
4. 仅当不会影响结果质量时才做 Token 优化。优先级固定为：需求理解 → 结果正确 → 安全与数据可靠 → 验证充分 → 可维护可追溯 → 强模型 Token → 执行速度。

### 2.1 `blocked` 状态的进入与解除

`global_state = blocked` 表示任务**暂停等待外部条件**。注意：per-pipeline `暂停` 是单条生产线暂停，全局 `blocked` 才是真无路可走。

- **pipeline `暂停`**: 仅影响单条生产线。主编排仍活跃，其他 pipeline 继续推进。
- **`global_state = blocked`**: 全局阻塞。主编排仍能接收用户输入并列出故障原因，但无法自动推进。只在真无路可走时进入。

`blocked_reason` 字段移到 STATE.json top-level。

进入条件（global_state 切到 blocked）：

| 触发场景 | 原因 | 解除条件 |
|---|---|---|
| 用户主动说"先暂停/先做别的"（所有 pipeline 都暂停） | 用户有其他事 | 用户说"恢复 / 继续" |
| 关键依赖不可用（DeepSeek V4 Pro 计划入口不可用，且主编排被禁止直接写 PLAN） | 没有 plan agent | 恢复计划入口，或用户明确缩小范围后重新启动 |
| 关键依赖不可用（真机/模拟器不可用，验证无法进行） | 缺测试环境 | 设备/AVD 就绪 |
| 真机验收中用户挂断/出门/回复"晚点再说" | 等用户回来 | 用户回来确认 |
| 同一类别编译/测试反复失败 ≥ 3 次 | 不可稳定收敛 | 标 `blocked`, 提示降级方案或拆类别 |
| 关键外部 API 不可用（联网/支付/三方SDK） | 缺外部资源 | API 恢复 |
| Plan Agent 反复 PLAN_GAP 2 次以上 | 需求定义不清 | 用户补充需求细节 |

**进入 blocked 时的强制动作**：

```bash
# 1. 把 global_state 标为 blocked
# STATE.json top-level 加字段: blocked_reason, blocked_at
# 2. 记录到 .ai-work/runs/<task>/BLOCKED.md
# 3. 向用户报告: "任务已 block, 原因: X, 解除需要: Y, 等你确认"
# 4. 不得自行 unblock - 等待用户明确指令
```

**解除 blocked 的强制动作**：

```bash
# 1. 用户明确说"恢复/继续/解除"
# 2. 删除 STATE.json 的 blocked_reason
# 3. global_state 回到 active, pipeline 从 previous_state 继续
# 4. 在 BLOCKED.md 记录解除时间和原因
```

**禁止**：
- 主编排"觉得"用户意思 = 自行 unblock
- blocked 后继续推进任务（绕过 block 状态）
- 修改 STATE.json 时不记录 blocked_reason

### 2.2 暂停 —— 显式编号列出所有 pipeline

当用户说"停"/"暂停"/"先停下"/"hold"时，主编排**不得直接改状态**。必须先:

1. 读取 STATE.json 所有 pipeline
2. 列出每个 pipeline 的编号、状态、当前在干什么:
   ```
   当前 active pipelines:
   #1 pipeline-login-fix: 开发 (developer 正在修 LoginActivity.kt, last commit: abc1234)
   #2 pipeline-permission: 计划 (等待 planner 返回 PLAN.md)
   #3 pipeline-ui-tweak: 测试 (tester 跑 instrumentation test)

   请指定: "停 #N" 或 "停全部"
   ```
3. 等用户精确说"停 #N" 或 "停全部" 后才执行
4. `暂停` pipeline 记录 `previous_state` 以便后续恢复
5. 如果用户说"停全部"，所有 pipeline 切 `暂停`。如果所有 pipeline `暂停` 且无新任务，`global_state` 仍保持 `active`（主编排仍能接收指令）

恢复:
- 用户说"恢复 #N" → pipeline 从 `previous_state` 继续
- 用户说"恢复全部" → 全部恢复

### 2.3 主编排永远 receptive

`global_state = active` 是常态。即使:
- 所有 pipeline 都是 `暂停`
- 所有 pipeline 都是 `已完成`
- 正在等待 planner/tester/reviewer 返回

主编排者仍能接收用户输入并响应。`global_state = blocked` 只在极少数情况下使用（Codex 0 额度 + 无 fallback / 网络断 / 关键依赖坏），且即使 `blocked` 也能接收用户输入，只是无法自动推进。

主编排者收到用户输入后:
1. 如果 `global_state = active` → 正常处理（切 pipeline / 新建 pipeline / 报告进度）
2. 如果 `global_state = blocked` → 先报告阻塞原因，再处理用户指令

## 3. 钩子强制执行

以下钩子是**强制门禁**，违反任一条应立即停止并纠正。完整钩子定义见 `HOOKS.md`。

| 钩子 | 触发时机 | 规则 |
|---|---|---|
| `plan_must_be_agent` | 需要生成 PLAN.md | **主编排者禁止自己写正式 PLAN.md**。默认由 DeepSeek V4 Pro planner 生成；OpenCode + oh-my-openagent 可用 `hyperplan` / plan wrapper 承载。主编排者只能写 `plan-input.md`、review、修正边界条件、批准。 |
| `planner_output_visible` | DeepSeek / OpenCode / OMO 计划代理返回 | 计划代理输出必须**完整展示**在主编排者的输出中。关键日志、结果摘要、错误信息一律不得静默丢弃。 |
| `plan_review_or_defer` | PLAN.md 生成后、进入开发前 | 优先调用 Codex/GPT 做二次计划审查：第一轮 GPT-5.4，第二轮复审/升级审查 GPT-5.5。可用时必须保留 `PLAN_REVIEW.round1.gpt-5.4.md` / `PLAN_REVIEW.round2.gpt-5.5.md` 原始输出；无额度时必须有 `DEFERRED_CODEX_REVIEW.md` 且 `plan_review_status = deferred_due_to_quota`。 |
| `raw_outputs_must_be_preserved` | 任一角色产出文档/审查/报告后 | Planner、reviewer、developer、tester、rescue 的原始输出禁止覆盖。修订只能新增 `v2`、`round2`、`patch`、`resolution` 或 `superseded` 文件；当前入口文件必须可追溯到原始版本。 |
| `agent_runtime_visible` | 启动 Codex / OpenCode / OMO plan/review/implement 脚本 | 脚本或运行目录必须立刻产出 `status.json`、stdout/stderr 日志路径、最后活动时间、静默秒数和超时状态。主编排者不得盲等。 |
| `stage_entry_check` | 进入新阶段 | 检查前置阶段产物文件是否存在且非空。缺失则禁止进入。 |
| `pre_commit_gate` | 提交代码前 | 检查 VERIFICATION_REPORT 存在、测试通过、无未关闭的 BLOCKER 级 issue。 |
| `max_retry_gate` | 第 3 次相似修复 | 同一问题同一方案最多 2 轮。第 3 次必须升级假设、模型或会话。 |
| `parallel_safety_check` | 启动并行类别 | 检查依赖图，确认无共享数据库结构、核心状态、关键文件冲突。 |
| `post_task_reflection` | 任务完成 / 类别关闭 | 编写 AUTO_DEV_LEARNINGS.md，记录踩坑、有效命令、可沉淀规则。 |

### 钩子执行流程

每个阶段切换时，主编排者必须自检：

1. 当前阶段是什么？
2. 前置钩子是否全部通过？
3. 如果钩子未通过 → 停止，先满足钩子条件
4. 钩子通过 → 继续

### 计划/执行代理运行可观测性约定

凡是由脚本启动的 DeepSeek / OpenCode / oh-my-openagent / 可选 GPT plan / review / implement，都必须满足以下约定：

1. 启动即写出 `status.json`，至少包含：
   - `status`
   - `started_at`
   - `last_heartbeat_at`
   - `last_activity_at`
   - `silent_for_seconds`
   - `output_file`
   - `stdout_file`
   - `stderr_file`
2. 主编排者在发起后第一时间向用户展示：
   - 状态文件路径
   - stdout/stderr 日志路径
   - 当前状态（`running` / `silent` / `timed_out` / `failed` / `completed`）
3. 禁止静默等待：
   - 超过 600 秒无活动 → 状态必须标成 `silent`
   - 达到脚本定义的最大运行时长 → 状态必须标成 `timed_out`
4. 若状态变成 `silent` 或 `timed_out`，主编排者必须汇报卡住位置、日志路径和下一步处理，不能只说"还在跑"。

## 4. 阶段路由

按当前阶段按需读取子 skill，不要一次全部塞进上下文：

- 需求澄清：`skills/requirements-brainstorming.md`
- 代码调研：`skills/code-research.md`
- 分类计划：`skills/category-planning.md`
- 类别开发：`skills/category-development.md`
- 测试验收：`skills/testing-and-acceptance.md`
- 系统调试：`skills/systematic-debugging.md`
- wave 集成：`skills/wave-integration.md`
- 完成验证：`skills/verification-before-completion.md`

全局规范：

- `WORKFLOW.md`
- `ROUTING.md`
- `MODEL_ROUTING.md`
- `REPORT_FORMATS.md`

## 5. 核心约束

1. 先澄清、调研、分类，再规划和开发。
2. 机械性搜索、目录扫描、调用链整理优先交给调研代理；主编排负责判断事实和作出决策。
3. 最多并行 5 个类别，但不能强行凑满；先画依赖图，再按耦合度、模型额度、验证压力动态决定 wave。默认建议 1–5 路。**同类串行，不同类并行**：只有低耦合的不同类别才允许同批并行。
4. 每个类别是一条生产线：`PLAN -> PLAN_REVIEW -> PLAN_REVIEW_RESOLUTION(if needed) -> TEST_TARGET -> IMPLEMENT -> TEST -> CODE_REVIEW -> ACCEPTANCE`。`PLAN.md` 生成后优先由 Codex 做二次计划审查；是否复用会话取决于执行框架，同框架/返工可复用，跨框架用文件交接。`plan_status = approved` 且（`plan_review_status = approved` 或 `deferred_due_to_codex_quota`）后才能进入开发。Codex/GPT 必须在对应节点介入：Codex 计划审查在 `PLAN_REVIEW`，Codex 代码审查在 `CODE_REVIEW`；无额度则记录并跳过，不阻塞默认流程。
5. 每个并行类别必须独立 worktree、branch、责任身份和提交。
6. **责任身份不共享对话，只复用同一责任身份的原会话**：planner、plan reviewer、developer、tester、rescue 不能在同一对话里互相切换自审。Planner 与 plan reviewer 是不同责任身份：默认 DeepSeek V4 Pro planner 负责生成/修订 PLAN；第一轮 plan reviewer 用 GPT-5.4 提出计划问题；第二轮复审/升级审查用 GPT-5.5。review 意见必须回传 planner 裁决，成立则修订 PLAN/PLAN_PATCH，不成立则写明证据。Developer 修自己的代码改动；原 reviewer/tester 回到原审查/测试会话复验，直到 issue 关闭。固定的是责任闭环，不是把所有身份塞进一个聊天窗口。
7. **所有角色原始输出必须保留，禁止覆盖**：每一轮 PLAN、PLAN_REVIEW、PLAN_REVIEW_RESOLUTION、PLAN_PATCH、IMPLEMENTATION_REPORT、TEST_REPORT、CODE_REVIEW、RESCUE_REPORT 都必须保留原始版本。后续修改只能新增版本文件，不能把上一轮原文抹掉。
8. 原会话优先恢复；必要时可换新会话或升级模型，但新会话必须重新读文件证据。
9. 开发或测试首次进入类别、计划实质变化或新会话接手时，必须完整阅读：
   - `REQUIREMENTS.md`
   - `CODE_CONTEXT.md`
   - `DECISIONS.md`
   - `PLAN.md`
   - `PLAN_REVIEW.md`
   - 当前开放问题与 `HANDOFF.md`
10. 不能用摘要替代完整计划阅读。
11. 公共接口、数据结构、状态机基础、迁移、高权限、跨日/时间、后台恢复等节点完成后，必须先做关键中途检查。
12. **测试先行**：凡是可测试的需求，计划阶段必须先定义测试靶子和验收命令；进入开发后必须先写失败测试、最小复现、日志断言或可执行验证脚本，再写实现。测试即"靶"——先定义"怎样算通过"，再射箭。实现完再补测试不算测试先行。PLAN.md 的验收标准必须可被自动化检验，不能只是文字描述。
13. 同一问题最多自动两轮相似修复；第二次仍失败必须升级假设、证据、模型或会话。
14. 完成前必须记录新鲜验证证据：`VERIFIED_COMMIT`、`VERIFICATION_COMMAND`、`VERIFICATION_TIME`、`EXIT_CODE`、`RESULT_FILE`、`PROJECT_SPECIFIC_TEST_STATUS`（可选，由包装层定义，如 Android 的 `DEVICE_TEST_STATUS`）、`REMAINING_RISKS`。

### 5.1 责任身份、会话连续性与同模块追加问题

本规则对 Superpowers 的"fresh subagent"做本项目适配：**同类别是一条串行生产线，始终复用同一条文件化上下文；工具会话只在同一责任身份内复用**。开发会话用于实现和返工，审查/测试会话用于发现问题和复验关闭；不同责任身份不得共用同一对话自审。


#### 原始输出保留

- 每个责任身份的原始输出都是后续调查、复盘、第二轮计划和返工归因的证据，禁止覆盖。
- 推荐命名：`PLAN.v1.md`、`PLAN_REVIEW.round1.gpt-5.4.md`、`PLAN_REVIEW.round2.gpt-5.5.md`、`PLAN_REVIEW_RESOLUTION.round1.md`、`PLAN_PATCH.v2.md`、`CODE_REVIEW.round1.gpt-5.4.md`、`CODE_REVIEW.round2.gpt-5.5.md`。
- `PLAN.md` / `PLAN_REVIEW.md` 可以作为当前入口或索引，但必须写明指向哪个原始版本，不能只保留改写后的最终稿。

#### 会话复用边界

- 文件化上下文永远复用：`PLAN.md`、`PLAN_REVIEW.md`、`HANDOFF.md`、`FOLLOWUP-<n>.md`、commit 和测试报告是跨代理共同记忆。
- 工具会话不跨框架复用：Claude、Codex CLI、OpenCode/OMO 是不同运行框架，不能假设共享同一个聊天上下文。
- 当前回合的 `PLAN` 和 `PLAN_REVIEW` 若分别由不同框架执行，只能通过文件交接；不得写成"复用同一会话"。
- 用户实测反馈、同模块追加问题、二次计划修订、多次救火，若仍在原类别内，优先回到对应的原责任会话继续：原 developer 修，原 reviewer/tester 复验，原 planner 接收 Codex PLAN_REVIEW，裁决意见是否成立，并修订 PLAN/PLAN_PATCH。

#### Plan review 回传规则

`PLAN_REVIEW.md` 是 Codex plan reviewer 的审查意见，结论必须先回传 planner / 计划 owner（默认 DeepSeek V4 Pro）：

- `approved`：planner 确认后进入 `TEST_TARGET`。
- `changes_required`：planner 输出 `PLAN_REVIEW_RESOLUTION.md`，逐条接受/驳回 Codex 意见；接受项必须修订 `PLAN.md` 或 `PLAN_PATCH.md`，然后优先交原 Codex reviewer 复审。
- `blocked`：主编排介入，判断是需求不清、调研不足、计划缺口还是模型能力不足。

不得让 developer 直接根据 `PLAN_REVIEW.md` 改代码；计划问题先由 planner 消化成可执行计划，再进入测试先行和开发。

#### 同类别同模块：原责任会话优先

- 同一类别、同一模块、同一状态机链路的问题，默认回到对应原责任会话继续处理，不要为了形式重新开全新会话。
- 原开发者最了解前因后果，所以开发缺陷由原 developer 修；原测试者/审查者最了解失败现象和复验路径，所以问题关闭由原发现者复验。
- "谁开发谁修，谁发现谁验证关闭"表示责任闭环：修复和复验是两条责任线，不能让 developer 自己宣布 reviewer/tester 的问题已关闭。

#### 什么时候必须独立新会话

仅以下场景才优先新会话：

1. 用户明确启用 skill 开始下一批需求，或显式结束/归档上一个对话。
2. 原会话上下文明显污染，反复忽略证据或重复同一错误方案。
3. 原责任会话不可恢复。
4. 第 3 轮相似返工在同一生产线内换假设后仍不收敛，需要换模型或换审查视角。
5. 跨类别合并冲突、架构级判断或高风险外部第二意见需要真正独立视角。

注意：用户反馈后的二次计划修订、代码审查、多次救火本身不构成新会话理由；默认仍在同类别生产线内完成。但复用必须按责任身份发生：原 developer 返工，原 reviewer/tester 复验，原 rescue 继续同一救火线索；跨身份和跨框架只通过文件交接。

#### 同模块追加问题：必须走 planner，不得直接改代码

用户在实测中反馈的同模块 bug/问题，**无论看起来多简单**，都必须经过 planner：

```text
USER_REPORT_SAME_MODULE_ISSUE
  -> append ISSUES.json
  -> update category/FOLLOWUP-<n>.md
  -> write plan-input.md or PLAN_PATCH.md (描述根因 + 方案)
  -> DeepSeek V4 Pro planner 审查 / 生成修订计划
  -> planner approved → 才允许改代码
  -> if crosses category/interface/state-machine boundary: return to CATEGORY_DISCOVERY
```

- 即使新问题仍属于同一类别/同一模块，也**必须先写书面方案，经 planner 审查批准后再改代码**。不得因为"同模块"就直接动手。
- `PLAN_PATCH.md` 是**强制**的，不是"必要时"才写。每次用户反馈 bug 都必须有对应的 PLAN_PATCH 或 plan-input。
- 由 DeepSeek V4 Pro planner 做定点审查；主编排者不得自己审查自己的方案。
- 只有当新问题跨模块、跨公共接口、影响状态机基础或改变原验收标准时，才重新分类并重新计划。

#### 子代理交接粒度

子代理之间允许传递**文件路径 + 简短状态**，不需要搬运全文：

```text
handoff: CAT-2 -> CAT-2 tester
read:
- CAT-2/PLAN.md
- CAT-2/PLAN_REVIEW.md
- CAT-2/IMPLEMENTATION_REPORT.md
- commit: abc1234
focus:
- verify desktop -> target app relaunch lock path
- check logs containing LockState.RestEnd
blocked:
- none
```

主编排只需要收到进度摘要：当前步骤、关键文件路径、commit hash、阻塞点、下一步。长文档仍以文件为准。

#### 子代理 prompt 必须含原始 INPUT，不含主编排解读

在向子代理派遣任务时，prompt 中必须包含：

1. **原始 log**（编译输出、lint 错误、logcat、崩溃堆栈、测试失败输出等），原文照贴
2. **用户原话**（用户反馈 bug 的原始消息、用户需求原文），原文照贴
3. **相关文件路径列表**（需要读取的文件）
4. **简短任务描述**（1-3 句话，只说做什么，不解释为什么、不预判根因）

**禁止**在子代理 prompt 中加入：
- 主编排的根因推测（"我觉得是 X 导致 Y"）
- 主编排的方案建议（"你可以试试改成 Z"）
- 主编排对原始 log 的过滤/摘要（"错误大概就是 X 有问题"）

**原因**: 子代理需要基于原始事实做独立判断。主编排的解读可能引入偏见，导致子代理走弯路。用户原话: "你要给出原始的一个信息给子代理不能影响他的判断"。

**正确示例**:
```
INPUT:
- 用户原话: "点击开始按钮后闪退，logcat 报 NullPointerException"
- 原始 logcat: (贴完整堆栈)
- 相关文件: app/src/main/java/com/ironwill/ui/StartButton.kt
- 任务: 定位并修复点击开始按钮导致的 NullPointerException
```

**错误示例**:
```
INPUT:
- 用户说开始按钮闪退，我猜是 Intent 没初始化导致的
- 你去 StartButton.kt 里加个 null check 应该就行了
```

### 5.2 子代理派遣协议 —— Agent label + 终端 echo 必须显式声明角色+最底层实际模型名

每次用 Agent 工具派遣子代理时，**label 字段必须**使用以下格式，不得省略模型名。模型名必须用**终端显示名**（最底层实际模型），不是内部代号：

```
[角色:终端显示模型名] 任务简述
```

**终端显示模型名对照表**：

| 终端显示 | `model=` 参数 | 实际运行 |
|---|---|---|
| `deepseekV4pro` | `fable` | Claude Fable 5 (deepseek-v4-pro) |
| `opus` | `opus` | Claude Opus 4.8 |
| `sonnet` | `sonnet` | Claude Sonnet 4.6 |
| `haiku` | `haiku` | Claude Haiku 4.5 |
| `codex` | (Codex CLI `codex exec`) | GPT-5.4 / GPT-5.5 (Codex 内部) |
| (主编排, 默认不传) | (不传 `model`) | MiniMax-M3[1m] |

**Agent 派遣**（通过 Agent 工具）：

| 角色 | 强制 label 前缀 | 说明 |
|---|---|---|
| 计划代理 | `[planner:deepseekV4pro]` | 生成/修订 PLAN.md、PLAN_PATCH.md |
| 开发代理 | `[developer:sonnet]` (一般) / `[developer:opus]` (高风险) | 按已批准 PLAN 实现代码、自测、原子 commit |
| 测试代理 | `[tester:sonnet]` (写测试) / `[tester:haiku]` (跑测试) | 构建、测试、验收、复验，不改生产代码 |
| 调研代理 | `[researcher:haiku]` | 目录整理、文件定位、调用链梳理 |
| 一轮计划审查 | `[reviewer:codex]` | 第一轮审查 PLAN.md (Codex CLI 内部 gpt-5.4)，输出 PLAN_REVIEW.round1 |
| 二轮复审/升级审查 | `[reviewer:codex]` | 返工后第二轮复审 (Codex CLI 内部 gpt-5.5)，禁止退回 gpt-5.4 |
| 代码审查 | `[reviewer:codex]` | 审查关键 diff / 高风险代码 (Codex CLI 内部 gpt-5.4) |

**Codex CLI 调用**（通过 Bash 工具，走 `run-codex-*.ps1`）：

| 用途 | 触发时机 | Wrapper + 模型 | 终端显示 | 输出文件 |
|---|---|---|---|---|
| Codex 计划审查 | PLAN.md 首次生成后 | `run-codex-review.ps1` **`-Model gpt-5.4`** | `[reviewer:codex]` | `PLAN_REVIEW.gpt-5.4.md` |
| Codex 计划审查 **（升级）** | **上个交付周期用户反馈了 bug**，planner 出了新的 PLAN/PLAN_PATCH | `run-codex-review.ps1` **`-Model gpt-5.5`**（禁止退回 gpt-5.4） | `[reviewer:codex]` | `PLAN_REVIEW.gpt-5.5.md` |
| Codex 代码审查 | 实现+测试完成后 | `run-codex-code-review.ps1` **`-Model gpt-5.4`** | `[reviewer:codex]` | `CODE_REVIEW.gpt-5.4.md` |
| Codex 救火 | 多轮返工仍失败、根因不清 | `run-codex-rescue.ps1` **`-Model gpt-5.5`** | `[reviewer:codex]` | `RESCUE_REPORT.md` |

**"一轮"和"二轮"不是同一个 plan 来回审，而是不同的交付周期**：

```
交付周期 1:  PLAN → gpt-5.4 审一次 → 改 → 实现 → 测试 → 交付
                                                           ↓
                                               用户反馈 bug（第一轮交付失败）
                                                           ↓
交付周期 2:  PLAN_PATCH → gpt-5.5 审（升级！因为第一次没拦住）→ 改 → 实现 → 测试 → 交付
```

| 场景 | 模型 | 原因 |
|---|---|---|
| 全新任务、首次出 PLAN | `gpt-5.4` | 正常审查 |
| **上个周期用户反馈了 bug**，planner 出了新的 PLAN/PLAN_PATCH | `gpt-5.5` | 上一轮 gpt-5.4 没拦住，升级模型 |
| 同一类别之前交付过但返工了 → 再次审查 | `gpt-5.5` | 同上，已失败的链路必须升级 |

> **简单记法**：第一次交付 = gpt-5.4 审。用户说没改好 → 第二次交付 = gpt-5.5 审。 |

**Codex 调用强制规则**：

- 主编排者在 Bash 执行 Codex 命令前，**必须先向用户报告**：`Codex 调用: [用途, 模型: gpt-5.4/gpt-5.5, 输入文件, 预期输出文件]`
- Codex 返回后，必须展示 stdout 中的模型标识行
- 禁止黑箱调用 Codex——用户必须能看到用的是哪个模型

**示例**：

```
Agent label: "[planner:deepseekV4pro] 为 CAT-1 (锁屏闹钟UI修复) 生成 PLAN.md"
Agent label: "[reviewer:codex] 审查 CAT-1 PLAN.md — 需求覆盖+文件范围+测试先行+风险"
Agent label: "[reviewer:codex] 复审 CAT-1 PLAN_PATCH.v2.md — 第一轮未通过的返工审查 (内部 gpt-5.5)"
Agent label: "[developer:sonnet] 实现 CAT-1 — 按 PLAN.md 修改 window_alarm_overlay.xml"
Agent label: "[tester:sonnet] 验收 CAT-1 — 构建+ADB安装+logcat验证"

终端 echo:
派 [planner:deepseekV4pro] 为 CAT-1 生成 PLAN.md
派 [reviewer:codex] 审查 CAT-1 PLAN.md (内部 gpt-5.4)
派 [developer:sonnet] 实现 CAT-1
派 [tester:sonnet] 验收 CAT-1
```

**禁止**：
- 省略模型名：`[planner]` ❌ → 必须写 `[planner:deepseekV4pro]`
- 模型名用内部代号：`[planner:deepseek-v4-pro]` ❌ → 必须用终端显示名 `[planner:deepseekV4pro]`
- 主编排者自己当 planner：计划只有 DeepSeek V4 Pro (通过 fable agent) 能做
- 主编排者自己当 developer：主编排者**不是 developer**，源码修改必须 dispatch developer 子代理
- 主编排者自己当 reviewer：**禁止用任何 Claude 模型 (opus/sonnet/haiku/fable) 做 review**。reviewer 唯一 = Codex CLI (内部 gpt-5.4/gpt-5.5)
- 返工后用 gpt-5.4 审查第二轮：第一轮失败的，第二轮必须升级到 Codex CLI (内部 gpt-5.5)
- 主编排者直接 Write/Edit 源码代替 dispatch developer：这会触发 Gate 1 阻断
- Codex 黑箱调用：不报告模型、不展示 stdout 模型标识行 ❌
- 派单时不 echo 实际模型名：每次 dispatch 必须在终端 echo "派 [角色:模型名] 任务简述"

## 6. 状态文件

主状态优先使用（`{STATE_DIR}` 由调用方 SKILL.md 定义）：

- `{STATE_DIR}/STATE.json`
- `{STATE_DIR}/ISSUES.json`
- `{STATE_DIR}/runs/<task-id>/<category-id>/manifest.json`

兼容性文件：

- `{STATE_DIR}/ORCHESTRATOR_STATE.json`
- `{STATE_DIR}/AGENT_REGISTRY.json`
- `{STATE_DIR}/ISSUE_REGISTRY.json`
- `{STATE_DIR}/waves/wave-<n>/INTEGRATION_STATE.json`

## 7. 默认执行顺序

```text
ENV_CHECK
-> REQUIREMENTS_BRAINSTORMING
-> CODE_RESEARCH
-> CATEGORY_PLANNING   ← 此处触发 plan_must_be_agent 钩子
-> PLAN_REVIEW         ← 此处触发 plan_review_or_defer 钩子
-> TEST_TARGET         ← 新增: tester 先写失败测试 + RED 报告 (TDD 测试靶)
-> CATEGORY_DEVELOPMENT
-> TESTING_AND_ACCEPTANCE
-> WAVE_INTEGRATION
-> VERIFICATION_BEFORE_COMPLETION
```

如果当前任务是续跑，先读 `STATE.json`、`STATUS.md`、`CURRENT_STATUS.md`、`HANDOFF.md`，再进入对应阶段。

## 8. System 层门禁（PreToolUse Hook）

本 Skill 通过 `scripts/auto_dev_guard.py` 实现系统级 PreToolUse 门禁。以下行为会被**系统阻断**（不是提示，是拒绝工具调用）：

| 门禁 | 阻断条件 |
|---|---|
| Gate 1 | 未批准计划，或 Codex 二次计划审查既未通过也未记录延期时，Write/Edit/MultiEdit 到 `app/` `src/` `lib/` `core/` `packages/` |
| Gate 1.5 | V4 schema 下, 当前 pipeline `state` = `计划` / `已完成` / `暂停` 时改源码; 或 `state` ∈ {`测试靶`,`开发`,`测试`,`验收`} 但 `test_target_report` 不存在 (TDD 测试靶门禁) |
| Gate 2 | 主编排者直接 Write/Edit `plan.md` 或 `plan.meta.json`；正式计划必须来自 DeepSeek V4 Pro / OpenCode/OMO 计划代理 |
| Gate 3 | 无 `verification-report.md` 时执行 `git commit/merge/push` 或改 STATE 为 done |
| Gate 4 | Write/Edit 到 `plan.md` `implementation.md` `test-report.md` `review.md` 等长文档 |

**主编排者可以做的事**（不受阻断）：
- 生成 `REQUIREMENTS.md`、`CODE_CONTEXT.md`、`DECISIONS.md`、`plan-input.md`
- 调用当前项目允许的计划 / 审查代理入口；默认使用 DeepSeek V4 Pro planner + Codex reviewer，OpenCode/OMO 路线使用 `hyperplan` / `run-opencode-plan` / `run-omo-plan` 等包装层，并保持运行可观测
- 更新 `STATE.json` 的阶段和状态字段
- 记录文件路径 + 摘要，不搬运全文

完整门禁定义见 `HOOKS.md`，guard 脚本见 `scripts/auto_dev_guard.py`。

## 9. STATE.json Schema (V3_1_6 / schema_version=4)

```json
{
  "task_id": "20260708-xxxx-xxx",
  "schema_version": 4,
  "global_state": "active",
  "blocked_reason": null,
  "pipelines": {
    "<pipeline_id>": {
      "category": "<category>",
      "state": "计划",
      "previous_state": null,
      "plan_status": "pending",
      "plan_file": "<path>",
      "reviewer_status": "pending",
      "test_target_report": null,
      "last_commit": null,
      "branch": "<name>",
      "worktree": "<path or null>",
      "created_at": "2026-07-08T00:00:00+08:00",
      "updated_at": "2026-07-08T00:00:00+08:00"
    }
  },
  "current_pipeline": null,
  "verification_status": "pending",
  "created_at": "",
  "updated_at": ""
}
```

**pipeline 状态枚举** (7 状态):

```
计划 → 测试靶 → 开发 → 测试 → 验收 → 已完成
  ↑                ↓
  └────────────── 暂停
```

**global_state 枚举**:

| 值 | 含义 | 主编排能接收? |
|---|---|---|
| `active` | 主编排在跑，至少一个 pipeline 不为 `暂停` | 是 |
| `blocked` | 真无路可走 | 是，还能接收用户输入，但无法自动推进 |

**7 状态机规则**:

```
新建 pipeline → 计划 (默认)
计划 → 测试靶 (plan approved)
测试靶 → 开发 (tester 写完失败测试 + RED 报告存在)
开发 → 测试 (代码 commit)
测试 → 验收 (测试绿)
验收 → 已完成 (用户通过)
验收 → 计划 (用户报 bug, 旧需求 re-plan)
任何 → 暂停 (用户显式说"停")
暂停 → 之前状态 (用户说"恢复")
```

**废弃字段映射** (V3 → V4 迁移):

| 旧字段 | 新位置 |
|---|---|
| `current_phase` | `global_state` + per-pipeline `state` |
| `current_category` | `current_pipeline` (pipeline_id) |
| `current_wave` | 保留在 pipeline 内，不在 top-level |
| `plan_status` (top-level) | 移到 pipeline 内 |
| `plan_review_status` (top-level) | 移到 pipeline 内 → `reviewer_status` |

迁移脚本：`skills/_shared/tools/migrate_state_v3_to_v4.py`


## 10. OpenCode / oh-my-openagent 桥接规则

当用户主要使用 OpenCode 且 oh-my-openagent 固定启用时，本 Skill 不再假设 Claude Code 的 Skill 入口一定会被触发。此时必须把核心规则下沉为项目级规则：

1. 项目根 `AGENTS.md`：写短规则，要求任何开发任务先读 `.omo/rules/auto-dev.md`。
2. `.omo/rules/auto-dev.md`：放本文件、`WORKFLOW.md`、`HOOKS.md` 的精简版规则。
3. OpenCode/OMO 执行时，仍保留本 Skill 的长处：Research First、主编排亲自分类、每类独立计划、受控并行、测试先行、工作树卫生、验证证据。
4. OMO 的强项用于运行时：rules injection、Team Mode、LSP、AST-Grep、background agents、DeepSeek V4 Pro `hyperplan` 计划；Codex 做二次审查、`ulw-loop` 持久循环。
5. 两者冲突时：以项目级安全门禁优先；不得因为 `ultrawork` 自动推进而跳过计划、测试、commit hygiene、final verification。

## 11. Skill 版本管理

本 Skill 受 Git worktree 版本管理。修改 Skill 前必须阅读 `SKILL_VERSIONING.md`。

- 当前稳定版：`auto-dev-current` / `multi-agent-core-current`
- 修改必须通过 change worktree（命名：`{skill}-change-YYYYMMDD-功能名`）
- 禁止直接修改 current
