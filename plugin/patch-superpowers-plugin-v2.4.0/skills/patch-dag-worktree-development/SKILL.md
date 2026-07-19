---
name: patch-dag-worktree-development
description: Use when an approved Patch Superpowers Core Plan and detailed Execution Task DAG are ready for dynamic scheduling, TDD implementation, Luna review, integration gates, and serialized dev admission.
---

# Patch DAG Worktree Development

入口必须通过 `${CLAUDE_PLUGIN_ROOT}/bin/patch-superpowers-validate-planning.py`，并具备已批准 Core Plan、详细 Plan、DAG、MUST_FOLLOW 覆盖、已关闭承重假设、已确认参考声明和用户批准记录。

- Claude Developer：插件 Agent `patch-superpowers:patch-tdd-implementer`
- Claude Integration Operator：`patch-superpowers:patch-integration-operator`
- Task/Integration Review：Codex CLI `gpt-5.6-luna + medium`
- 复杂修复计划：Codex CLI `gpt-5.6-sol + medium`

下游必须复用单一业务事实权威结果；未经用户批准不得改变其条件、语义、范围或消费者含义。真实环境验收必须观察正向路径、负向路径和功能存活，排除假绿。
