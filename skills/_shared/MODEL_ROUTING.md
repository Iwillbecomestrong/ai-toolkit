# MODEL_ROUTING — auto-dev 默认模型路由

## 默认分工

| 角色 | 模型 / 工具 |
|---|---|
| 日常主编排 | Claude Code 壳 + MiniMax M3 |
| 计划代理 | DeepSeek V4 Pro |
| 计划审查（首次交付） | **唯一 Codex CLI**（内部 gpt-5.4）；输出 `PLAN_REVIEW.gpt-5.4.md`；无额度时记录延期审查。**Claude 模型 (opus/sonnet/haiku/fable) 禁止做 reviewer** |
| 计划审查（返工升级） | **唯一 Codex CLI**（内部 gpt-5.5）；上一个交付周期用户反馈了 bug、planner 出了新的 PLAN/PLAN_PATCH 时使用；无额度时记录延期，不设置替代 GPT 环节。**Claude 模型禁止做 reviewer** |
| 开发代理 | MiniMax M3 |
| 测试代理 | MiniMax M3 |
| 更高风险增强 | GPT-5.5，有额度时才启用；无额度不阻塞 |

## 强制规则

- **reviewer 唯一 = Codex CLI**（内部 gpt-5.4 或 gpt-5.5）。Claude 模型 (opus, sonnet, haiku, fable) **禁止**承担 reviewer 角色。主编排者不得用任何 Claude 模型自审 plan 或自审代码。Codex 没额度 → 记录 `DEFERRED_CODEX_REVIEW.md`，不找 Claude 替代审查。
- 所有 auto-dev / auto-code-android-dev 任务在 `PLAN.md` 生成后都必须调用 Codex 做计划审查：首次交付用 gpt-5.4，上个周期用户反馈 bug 后重新 plan 用 gpt-5.5；无额度则记录延期审查。
- `PLAN.md` 生成后不得直接进入开发。
- GPT/Codex 有额度时必须保留原始审查文件。无额度时必须有 `DEFERRED_CODEX_REVIEW.md`，且 `plan_review_status = deferred_due_to_quota` 或 `deferred_due_to_codex_quota`。
- **返工 = 升级审查**：上一个交付周期用户反馈了 bug → 意味着之前的 plan+审查+实现链路已失败。planner 出的新 PLAN/PLAN_PATCH，审查**必须升级到 GPT-5.5**（有额度时），**禁止**再用 GPT-5.4。理由：GPT-5.4 已审过上一轮且没拦住问题，重复用它等于浪费额度。
- Codex/GPT 是计划审查与关键代码审查的首选代理；没有额度时跳过并记录延期，不把任务置为 blocked，不临时指定别的模型自审。
- 如果 Codex/GPT 因 usage limit 不可用，记录到 `{STATE_DIR}/CODEX_STATUS.json` / `GPT_REVIEW_STATUS.json` 和当前任务的 `DEFERRED_CODEX_REVIEW.md`。延期记录仅用于审计追溯，**不自动补跑**——任务已通过 MiniMax 开发/测试完成并交付，事后补审旧计划无意义。
- 计划阶段多审一次，优先于开发后返工。
- **计划只有 DeepSeek V4 Pro 能做**：任何情况下（首次计划、返工修订、PLAN_PATCH、用户反馈后重计划），计划的生成和修订只能由 DeepSeek V4 Pro planner 执行。主编排者、Codex、GPT、MiniMax 均不得代写 PLAN 或 PLAN_PATCH。Codex/GPT 只能审，不能写。
- **子代理派遣必须显式声明模型**：每次 Agent dispatch 的 label 必须用 `[角色:模型]` 格式（详见 SKILL_CORE.md §5.2）。主编排者自身不是 planner/developer/reviewer——必须 dispatch 对应模型的子代理。

## Codex 可选增强触发点

Codex 不应该等到流程末尾才看。它有额度时，在对应节点就介入：

1. `PLAN_REVIEW`：在 `PLAN.md` 生成后、开发前，Codex 做二次计划审查；不是等到最终验收才看。
2. `CODE_REVIEW`：在实现、测试和 commit 后，可对关键 diff / 高风险代码做 Codex 审查。
3. `RESCUE`：同类别多轮返工仍失败、根因不清或架构判断卡住时，可调用 Codex 救火。

Codex 不可用时：不重复盲试、不阻塞 DeepSeek 计划 + MiniMax 开发/测试流程，只记录延期审查项。

## 生产线规则

- 同一类别是一条串行生产线：`PLAN -> PLAN_REVIEW(gpt-5.4首次/gpt-5.5返工) -> TEST_TARGET -> IMPLEMENT -> TEST -> CODE_REVIEW -> ACCEPTANCE`。每个交付周期只审一次，模型选择看是首次交付还是返工。
- 同类串行，不同类并行；不同类别低耦合时最多 5 路并行。
- 二次计划审查、代码审查、多次救火默认复用同类别文件化上下文；会话复用只发生在同一责任身份内：原 developer 返工，原 reviewer/tester 复验关闭，原 planner 接收 Codex 审查意见，裁决并修订 PLAN/PLAN_PATCH；跨身份或跨框架只做文件交接。
- 只有用户开始下一批需求、显式结束上个对话、上下文污染、原会话不可恢复、跨类别架构判断或多轮同错不收敛时，才切新会话。
- 可测试需求必须先写失败测试、最小复现或可执行验证脚本，再写实现。


## 原始输出保留

每个角色的原始输出都必须保留，方便后续第二轮调查、第二轮计划、返工归因和复盘。禁止覆盖上一轮输出；修订只能新增文件。推荐命名：

- `PLAN.v1.md`、`PLAN.v2.md`
- `PLAN_REVIEW.round1.gpt-5.4.md`、`PLAN_REVIEW.round2.gpt-5.5.md`
- `PLAN_REVIEW_RESOLUTION.round<n>.md`
- `PLAN_PATCH.v<n>.md`
- `CODE_REVIEW.round1.gpt-5.4.md`、`CODE_REVIEW.round2.gpt-5.5.md`
- `IMPLEMENTATION_REPORT.<owner>.<round>.md`、`TEST_REPORT.<tester>.<round>.md`

`PLAN.md` / `PLAN_REVIEW.md` 可以作为当前入口或索引，但必须指向原始版本文件。
