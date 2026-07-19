---
name: patch-writing-plans
description: Use when approved software requirements and bounded evidence need a Sol core plan, user confirmation, and a detailed Execution Task DAG without early reference anchoring.
---

# Sol 两阶段规划与延迟参考

Planner 通过 Codex CLI 调用，不是 Claude Agent：

- Core / Detailed / Repair / Plan Patch：`gpt-5.6-sol + medium`
- 同根因三次失败后的架构复审：`gpt-5.6-sol + high`

实际模型由 `${CLAUDE_PLUGIN_ROOT}/config/model-routing.json` 唯一指定。

## 第一阶段：核心计划

首次 Sol 输入只允许：

- `MUST_FOLLOW_INDEX.md`
- `SPEC.md`
- `EVIDENCE_PACK.md`
- `ASSUMPTION_REGISTER.md`
- `DECISION_AUTHORITY_MAP.md`
- `REFERENCE_ONLY_PATHS` 的路径索引（不得读取正文）

输出：`CORE_PLAN_READY | VALIDATION_REQUIRED | RESEARCH_GAP | USER_DECISION_REQUIRED | REFERENCE_ACCESS_REQUIRED`。

只有无法从调查证据和代码逻辑形成方案时，才能申请定点读取参考路径。参考声明先标为 `UNVERIFIED_REFERENCE`，经验证成为 `CONFIRMED` 后才允许写入计划。

## 核心计划门禁

`CORE_PLAN.md` 只冻结：问题事实、根因、单一业务事实权威、承重假设、最小方案、影响范围、高层 Task 边界和 MUST_FOLLOW 覆盖。随后派 Claude `patch-superpowers:patch-plan-challenger` 对抗审查，并展示给用户批准。

## 第二阶段：详细计划

核心计划批准后，恢复同一个 Sol thread 生成 `PLAN.md` 与 `EXECUTION_DAG.json`。详细计划只能展开核心计划；若需改变路线、范围、权威判断、用户行为或承重假设，返回 `CORE_PLAN_REVISION_REQUIRED`。

详细计划再由 Claude Plan Challenger 做一致性审查，用户批准后才能开发。

## 单一业务事实裁决

同一业务事实只能有一个权威判断点；下游必须复用其结果。原判断不在本次范围时保持不变。若必须改变，必须先向用户说明当前判断、拟议变化、消费者、用户影响和回归风险，获得明确批准后统一修改原判断及消费者。
