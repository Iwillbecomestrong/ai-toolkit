# Shared Workflow — auto-dev / multi-agent-core

## 1. 主流程状态机

```text
INIT
  -> ENV_CHECK
  -> RESEARCH
  -> CATEGORY_DISCOVERY          ← 主编排者亲自分类，严禁委托计划代理
  -> BATCH_PLAN_BY_SUBAGENT      ← 每类独立启动 DeepSeek V4 Pro / OpenCode-OMO 计划代理
  -> MANDATORY_PLAN_REVIEW       ← 每类必须二次计划审查，防止计划错导致返工
  -> WAVE_LOOP
  -> FINAL_REGRESSION
  -> FINAL_ACCEPTANCE
  -> OPTIONAL_FINAL_INDEPENDENT_REVIEW
  -> COMPLETE
```

### CATEGORY_DISCOVERY（主编排者亲自执行，不可委托）

1. 主编排者基于 RESEARCH 阶段的产物（CODE_CONTEXT.md、调研报告），**亲自**阅读并理解每个 Bug/需求的代码范围
2. 按**文件耦合度**分组：改同一文件/同一模块的归入同一类
3. 识别依赖关系：A 类的输出是否是 B 类的输入
4. 产出 `CATEGORIES.md`，至少包含：
   - 每个类覆盖哪些 Bug/需求
   - 涉及哪些文件
   - 类之间的依赖关系（无依赖 / A→C / 共享文件冲突）
   - 推荐执行顺序和可并行组合
5. **严禁**将分类工作丢给 计划代理。分类是编排决策，不是机械劳动

### BATCH_PLAN_BY_SUBAGENT（每类独立计划代理）

1. 对 CATEGORIES.md 中的**每个类别**，独立启动一个计划代理。
2. N 个类别 = N 次计划代理调用；默认 DeepSeek V4 Pro planner，OpenCode + oh-my-openagent 场景可用 `hyperplan` / team plan 承载。
3. 每个计划代理只看到自己类别的需求、涉及文件、约束条件。
4. 每个类别产出独立的 `PLAN.md` + `plan.meta.json`。
5. 每个类别计划生成后，必须进入 MANDATORY_PLAN_REVIEW：第一轮优先调用 Codex/GPT-5.4 审查 `PLAN.md`；若 changes_required，planner 裁决并修订后，第二轮优先调用 GPT-5.5 复审。跨 Claude/Codex/OpenCode 时通过文件交接。GPT/Codex 无额度时记录延期审查，不阻塞当前开发；额度刷新后补跑。
6. 主编排者逐个 review `PLAN.md` + `PLAN_REVIEW.md`，检查跨类接口一致性，批准后进入 WAVE_LOOP。
7. **严禁**一个计划代理包揽所有类别的计划（会导致上下文污染、计划质量下降）。

`WAVE_LOOP` 展开为：

```text
WAVE_PREPARE
  -> START_UP_TO_5_CATEGORIES
  -> CATEGORY_LOOP (parallel where allowed)
  -> WAVE_INTEGRATION
  -> WAVE_CLOSE
```

`CATEGORY_LOOP` 展开为：

```text
CATEGORY_START
  -> CATEGORY_PLAN
  -> CATEGORY_PLAN_REVIEW      ← 第一轮 GPT-5.4 输出 PLAN_REVIEW；只提意见，不直接改 PLAN
  -> CATEGORY_PLAN_REVIEW_RESOLUTION  ← 若 changes_required，回传 planner 裁决并修订 PLAN/PLAN_PATCH
  -> CATEGORY_PLAN_REVIEW_ROUND2      ← 第二轮 GPT-5.5 复审修订后的 PLAN/PLAN_PATCH（有额度时）
  -> CATEGORY_TEST_TARGET      ← 先确定测试/验收靶子
  -> IMPLEMENT_LOOP            ← 先写失败测试/最小复现/可执行验证脚本，再写实现
  -> CATEGORY_TEST
  -> CATEGORY_CODE_REVIEW      ← 同一类别生产线内代码审查；Codex 有额度时可在此节点审关键 diff
  -> CATEGORY_ACCEPTANCE
  -> USER_DEVICE_ACCEPTANCE    ← Android/真机实测子阶段，不是必须新增 STATE 枚举
  -> CATEGORY_CLOSE
```

## 1.1 类别生产线模型

每个类别是一条串行生产线，不是一组可以在同类内部并行乱跑的子任务：

```text
同一类别生产线：
PLAN -> PLAN_REVIEW.round1.gpt-5.4 -> PLAN_REVIEW_RESOLUTION(if needed) -> PLAN_REVIEW.round2.gpt-5.5(if needed/available) -> TEST_TARGET -> IMPLEMENT -> TEST -> CODE_REVIEW -> ACCEPTANCE -> FOLLOWUP/REPAIR
```

Codex/GPT 在对应工位介入：第一轮二次计划审查放在 `PLAN_REVIEW.round1.gpt-5.4`，第二轮复审/升级审查放在 `PLAN_REVIEW.round2.gpt-5.5`，代码审查放在 `CODE_REVIEW`，复杂救火放在 `FOLLOWUP/REPAIR`。无额度时记录 `{STATE_DIR}/CODEX_STATUS.json` / `GPT_REVIEW_STATUS.json` 和 `DEFERRED_CODEX_REVIEW.md`，不改变生产线顺序，也不阻塞 DeepSeek 计划 + MiniMax 开发/测试流程。

规则：

- **计划审查回传**：GPT-5.4 / reviewer 负责第一轮提出计划问题，不直接改 PLAN；`changes_required` 必须回传原 planner，由 planner 判断是否成立并修订 `PLAN.md` / `PLAN_PATCH.md`；修订后**必须**由 GPT-5.5 做第二轮复审（有额度时），再进入测试靶子和开发。**禁止**用 GPT-5.4 做第二轮——第一轮已失败，GPT-5.4 已证明拦不住问题，第二轮必须升级模型。
- **同类串行**：同一文件、同一模块、同一状态机链路归入同一类别，按生产线顺序推进，不允许多个开发代理同时抢改。
- **异类并行**：只有不同类别、低耦合、无共享核心文件/状态/数据库/接口依赖时，才允许进入同一个 wave 并行，最多 5 路。
- **会话复用**：同类别生产线默认复用同一条文件化上下文。工具会话只在同一责任身份内复用：谁开发谁返工，谁发现谁复验关闭；planner/reviewer/developer/tester/rescue 不得在同一个对话里互相切换自审。PLAN 与 PLAN_REVIEW 若由不同责任身份或不同框架承载，只能通过 PLAN.md、PLAN_REVIEW.md、HANDOFF.md 交接。
- **用户追加同模块问题**：如果用户实测时补充同模块现象，追加到当前类别生产线的 `FOLLOWUP-<n>.md`，回原责任会话继续，不从零重跑首次流程。
- **换会话例外**：只有用户明确开始下一批需求/结束上个对话、原会话污染、原会话不可恢复、跨类别架构判断或多轮同错不收敛时，才换新会话。

### 1.2 会话复用边界

类别生产线的"复用"不是说 Claude、Codex、OpenCode 能共用一个聊天窗口，而是分两层：

| 层级         | 规则                                                                                                                        |
| ------------ | --------------------------------------------------------------------------------------------------------------------------- |
| 文件化上下文 | 永远复用同一类别目录下的`PLAN.md`、`PLAN_REVIEW.md`、`HANDOFF.md`、`FOLLOWUP-<n>.md`、报告、commit。                |
| 工具会话     | 只有同一责任身份 + 同一框架/同一命令行会话可恢复时才复用；跨责任身份或跨 Claude / Codex CLI / OpenCode+OMO 时只能文件交接。 |

具体规则：

- **计划审查回传**：GPT-5.4 / reviewer 负责第一轮提出计划问题，不直接改 PLAN；`changes_required` 必须回传原 planner，由 planner 判断是否成立并修订 `PLAN.md` / `PLAN_PATCH.md`；修订后**必须**由 GPT-5.5 做第二轮复审（有额度时），再进入测试靶子和开发。**禁止**用 GPT-5.4 做第二轮——第一轮已失败，GPT-5.4 已证明拦不住问题，第二轮必须升级模型。
- 当前同一回合内，`PLAN` 和 `PLAN_REVIEW` 若分别由不同框架执行，不称为"同一会话复用"，只称为"同类别文件化交接"。
- 用户反馈后的二次计划修订、同模块返工、多次救火，若原责任会话还可恢复，优先回原责任会话继续：原 developer 修，原 reviewer/tester 复验，原 planner 裁决 PLAN_REVIEW 并修订 PLAN/PLAN_PATCH。
- 若用户没有启用 skill 开始下一批需求，也没有显式结束上一条生产线，同类别问题默认继续原生产线，但仍按责任身份分会话/分工位推进。

## 2. 编排后端与角色模型

编排后端由各 SKILL.md 的 `--orchestrator=` 参数选择。子代理（开发者/测试者）的固定职责不受编排后端影响。

### 通用角色

| 角色                   | 职责                                                                                                                                                                  |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 主编排者               | 分类、调度、代理责任、状态恢复、返工升级、最终完成判断                                                                                                                |
| 开发者（子代理）       | 类别实现、代码修改、自测                                                                                                                                              |
| 测试者（子代理）       | 类别测试、验收、修复后回归                                                                                                                                            |
| 调研代理               | 目录整理、文件定位、调用链梳理、当前行为归纳                                                                                                                          |
| 计划代理（子代理）     | 类别计划、验收标准 —**默认由 DeepSeek V4 Pro planner 或 OpenCode/OMO hyperplan 生成 PLAN.md**                                                                  |
| 计划审查代理（子代理） | 二次计划审查 —**第一轮默认 GPT-5.4 输出 PLAN_REVIEW；第二轮复审默认 GPT-5.5。只提意见，不直接改 PLAN。changes_required 必须回传 planner 裁决并修订后才能开发** |

### 编排后端差异

各后端的具体模型分配参见各自 SKILL.md：

- **Claude 编排** → `auto-dev` SKILL.md
- **Codex 编排** → `multi-agent-core` SKILL.md（默认）
- **OpenCode 编排** → `auto-dev` SKILL.md（`--orchestrator=opencode`）+ `AGENTS.md` / `.omo/rules/**` 桥接

## 3. 文件流转

主会话长期状态只认：

- `Git`
- `{STATE_DIR}/STATE.json`
- `{STATE_DIR}/ISSUES.json`
- `{STATE_DIR}/runs/<task-id>/<category-id>/manifest.json`
- `CURRENT_STATUS.md`
- `HANDOFF.md`
- `DECISIONS.md`
- `BUGS.md`

### 原始输出不可覆盖

每个角色的原始输出都是追溯证据，禁止覆盖。当前入口文件可以更新，但原始版本必须保留：

- `PLAN.v1.md` / `PLAN.v2.md`
- `PLAN_REVIEW.round1.gpt-5.4.md`
- `PLAN_REVIEW.round2.gpt-5.5.md`
- `PLAN_REVIEW_RESOLUTION.round<n>.md`
- `PLAN_PATCH.v<n>.md`
- `IMPLEMENTATION_REPORT.<owner>.<round>.md`
- `TEST_REPORT.<tester>.<round>.md`
- `CODE_REVIEW.round1.gpt-5.4.md` / `CODE_REVIEW.round2.gpt-5.5.md`

`PLAN.md`、`PLAN_REVIEW.md`、`TEST_REPORT.md` 可以作为当前入口或索引，但必须指向对应原始文件，不能只保留最终改写版。

> `{STATE_DIR}` 由各自 SKILL.md 定义：auto-dev 使用 `.ai-work`，multi-agent-core 使用 `.collab-work`。

## 4. Research First

正式分类和计划前，默认先由调研代理做机械性调研：

- 目录整理
- 文件定位
- 调用链梳理
- 当前行为归纳
- 测试文件、日志路径定位
- 风险与未知项标记

研究结果必须区分：`CONFIRMED` / `INFERRED` / `UNKNOWN`

## 5. 受控并行

- 最大并行度为 5，但不强制凑满；默认根据耦合度、模型额度、验证压力在 1–5 路之间选择。
- 并行的是"不同类别"，不是同一类别内多个流程节点；同一类别内部按生产线串行推进。
- 只有低耦合的不同类别允许同批并行；同一类别、同一模块、同一状态机链路必须串行。
- 每个并行类别必须有独立 worktree、branch、类别目录和一条串行生产线；同一类别内部不得并行抢改，developer/tester/reviewer 只是生产线上的不同工位。

不允许直接并行的典型情况：

- 共享数据库结构
- 共享核心状态
- 共享关键文件
- 接口仍在变化
- 一个类别输出是另一个类别输入
- 多个类别同时修改跨日、后台服务或核心锁定链路

启动并行前 → 触发 `parallel_safety_check` 钩子。

## 6. 返工闭环

```text
TEST_FAIL or ACCEPTANCE_FAIL or INDEPENDENT_REVIEW_FAIL
  -> AGGREGATE_ISSUES
  -> ORCHESTRATOR_CHECK_CAUSE
  -> ROUTE_TO_OWNER
  -> REPAIR
  -> RETEST_AFFECTED_CATEGORY
  -> RECHECK_BY_DISCOVERER
```

规则：

- **返工 = 升级审查**：用户反馈 bug / 第一次实现未通过 → 意味着第一轮计划+审查+实现链路已失败。修订后的 PLAN/PLAN_PATCH 第二轮审查**必须**用 GPT-5.5（有额度时），**禁止**再用 GPT-5.4——GPT-5.4 已审过第一轮且没拦住问题，返工后重复用它等于浪费额度。无额度时记录延期到 `DEFERRED_CODEX_REVIEW.md`，额度刷新后补 GPT-5.5 审查。
- **计划审查回传**：GPT-5.4 / reviewer 负责第一轮提出计划问题，不直接改 PLAN；`changes_required` 必须回传原 planner，由 planner 判断是否成立并修订 `PLAN.md` / `PLAN_PATCH.md`；修订后**必须**由 GPT-5.5 做第二轮复审（有额度时），再进入测试靶子和开发。**禁止**用 GPT-5.4 做第二轮——第一轮已失败，GPT-5.4 已证明拦不住问题，第二轮必须升级模型。
- 谁开发谁修改；同类别/同模块默认回原开发会话继续，有始有终。
- 谁发现谁验证到关闭；原测试/用户实测反馈优先由原发现链路复验。
- 审查和测试代理默认不改生产代码。
- 第一次返工失败就检查问题出在哪。
- 同一问题最多自动两轮相似修复；第 3 轮 → 触发 `max_retry_gate` 钩子。
- 同模块追加问题先走 `FOLLOWUP-<n>.md` + 原责任会话；只有跨类别/接口/状态机边界才重新分类和重跑完整计划。

## 6.1 会话连续性与轻量交接

本流程不是每一步都强制 fresh agent。实际开发尤其是 Android 状态机、锁屏链路、后台恢复问题，更需要保留上下文。

### 默认策略

| 场景               | 会话策略                                                                                                                                               |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 同类别继续开发     | 恢复原开发会话                                                                                                                                         |
| 同模块用户追加问题 | 恢复原开发/测试会话，写`FOLLOWUP-<n>.md`                                                                                                             |
| 原测试发现问题     | 原测试会话复验到关闭                                                                                                                                   |
| 二次计划审查       | 审查者是独立责任身份；Codex 有额度时由 Codex 生成 PLAN_REVIEW。若后续同一个 reviewer 需要复审，可 resume 原 reviewer 会话；不得复用 planner 会话自审。 |
| 代码审查           | 审查者是独立责任身份；后续同一问题复审回原 reviewer/tester 会话；developer 只负责修，不负责关闭自己被指出的问题。                                      |
| 第 3 轮相似返工    | 先在同类别生产线内换假设；仍不收敛才换模型或换会话                                                                                                     |

### 子代理之间允许轻量传递

子代理可以直接传递文件路径和简短状态，不必所有细节都经主编排搬运。主编排只保留调度权和状态汇总权。

允许传递：

- 相关文件路径
- PLAN / PLAN_REVIEW / REPORT 路径
- commit hash
- 当前阻塞点
- 下一步验证命令

禁止传递：

- 大段复制 PLAN 全文
- 私下改变类别边界
- 私下决定跳过计划审查、测试或验收
- 多个代理自行合并同一文件冲突

### 用户实测 / 人工验收追加闭环

通用流程只定义追加闭环，不定义具体平台的设备验证字段。用户在人工验收、真机实测或业务实测中发现同模块追加问题时：

```text
USER_ACCEPTANCE_FAIL_OR_NEW_SAME_MODULE_ISSUE
  -> record USER_ACCEPTANCE_NOTES.md
  -> append ISSUES.json
  -> category/FOLLOWUP-<n>.md
  -> original developer repairs
  -> original tester or original finder re-verifies
  -> update TEST_REPORT.md / project-specific status
```

只有新增问题跨模块、跨公共接口、改变原需求或影响基础状态机，才回到 `CATEGORY_DISCOVERY` 重新分类。Android 的 `DEVICE_TEST_STATUS` / `USER_DEVICE_TEST_STATUS` 由 `auto-code-android-dev` 包装层补充定义。

## 7. 主编排介入节点

出现以下情况时，编排者必须介入：

- 第一次返工后仍未通过
- plan、review、test 标准明显不一致
- developer 连续给出相似错误方案
- 模型额度不足或明显能力不够

介入流程：

```text
REWORK_FAIL_ONCE
  -> ORCHESTRATOR_DIAGNOSE
  -> CLASSIFY_CAUSE (RESEARCH_GAP / PLAN_GAP / STANDARD_MISMATCH / DEVELOPER_EXECUTION / TEST_SYSTEM_ISSUE / ENVIRONMENT_LIMIT)
  -> 记录改进项（更新 WORKFLOW/ROUTING + 项目 memory）
  -> UPGRADE_RIGHT_AGENT_OR_MODEL
  -> RESUME_ORIGINAL_OWNER
```

## 8. 先易后难

这条保留你的长处：不要被复杂问题拖死。简单可收敛项先完成，复杂项最后升级模型或换代理。

- 当前类别先解决低耦合、可稳定收敛的问题。
- 复杂问题可 `SKIPPED_DEFER_NEXT_TIER`，先完成其他可解项。
- 最后再统一升级模型处理复杂项。

## 9. 集成波次

每个 wave 的标准流程：

```text
WAVE_PREPARE
  -> create isolated worktrees
  -> run up to 5 categories
  -> create integration worktree
  -> merge in planned order
  -> quick integration check after each merge
  -> wave integration test
```

集成问题处理：

- 单类问题查单类文档并交回原开发代理
- 双类冲突查两类文档并由主编排决定接口/顺序
- 真正三方问题才加载三类文档

## 10. OpenCode / oh-my-openagent 协同

当使用 OpenCode + oh-my-openagent 时，本 Workflow 不替代 OMO，而是约束 OMO：

- `ultrawork` / `ulw-loop` 负责持续推进，但必须在 `RESEARCH`、`CATEGORY_DISCOVERY`、`PLAN_APPROVAL` 之后才能改代码。
- `hyperplan` 适合承载 DeepSeek V4 Pro 的每类 PLAN 生成；Codex 二次审查，尤其是高风险状态机、后台任务、权限、数据库迁移。
- Team Mode 可承载并行类别，并行上限默认 5；MiniMax / OpenCode 额度充足时可以开满 5 路，但共享核心状态、数据库、关键文件、后台服务或跨日/时间逻辑时必须主动降并行。
- OMO 的 LSP / AST-Grep / grep_app / codegraph 用于 Research First，不替代主编排者分类。
- 所有 team member 的完成报告必须写入对应类别目录的 `manifest.json` / `HANDOFF.md`，不得只在终端口头报告。

## 11. 完成前验证

类别关闭前必须保留新鲜验证证据：

- `VERIFIED_COMMIT`
- `VERIFICATION_COMMAND`
- `VERIFICATION_TIME`
- `EXIT_CODE`
- `RESULT_FILE`
- `PROJECT_SPECIFIC_TEST_STATUS`（可选，由包装层定义，如 Android 的 `DEVICE_TEST_STATUS`）
- `REMAINING_RISKS`

提交前 → 触发 `pre_commit_gate` 钩子。

任务完成后 → 触发 `post_task_reflection` 钩子。

## 12. 工作树 commit 规范（强约束）

**目的**：防止 Agent 在 working tree 累积未提交改动 → linter/编辑器/session 中断时全丢（实测 100+ 行代码丢失事件）。

### `commit_step_gate`（每步强制）

任何源码/文档修改后，**必须**在同一 Agent 的下一步操作前：

```bash
git status --short                       # 确认本次修改范围
git add <精确文件>                       # 不要用 git add . / git add -A
git commit -m "<明确的 step message>"
```

**禁止**：

- 把多个步骤累积到 working tree 再一次性 commit
- 用 `git add .` / `git add -A`（会带进无关文件）
- "等真机验收再 commit"（真机前要 commit，否则丢失无恢复）

### `working_tree_audit`（任务/Agent 切换时强制）

Agent 退出、任务完成、子任务切换前**必须**：

```bash
git status --short                       # 输出必须为空，否则 commit 或 revert
```

**失败行为**：

- 任务结束 `git status` 不为空 → 不得声称"完成"
- Agent 报"已完成"但 `git log --oneline` 没有新 commit → 主编排必须强制重做或 commit

### 实施保障

- `scripts/auto_dev_guard.py` Gate 5: commit/push 前自动检查
- `auto-dev/SKILL.md` §commit_step_gate: 提示词层强制
- `auto-code-android-dev/SKILL.md` §android_commit_step_gate: Android 额外加编译验证
- OpenCode/OMO 场景：同样写入 `.omo/rules/auto-dev.md`，防止 `ultrawork` 长时间累积未提交改动
