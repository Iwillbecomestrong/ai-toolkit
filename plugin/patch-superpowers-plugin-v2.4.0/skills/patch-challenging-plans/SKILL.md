---
name: patch-challenging-plans
description: Use when a Sol core plan or detailed execution plan must be independently challenged before user approval or implementation.
---

# Claude 计划对抗审查

主 Claude 派插件 Agent `patch-superpowers:patch-plan-challenger`。它不写计划、不改代码，只攻击导致大规模返工的前提。

## Core Plan Challenge

检查：MUST_FOLLOW 覆盖、承重假设、单一业务事实裁决、权威变化用户批准、是否提前读取参考、参考声明是否 CONFIRMED、是否有更小方案、真实证据和功能死亡风险。

## Detailed Plan Consistency Review

检查详细计划是否忠实展开 Core Plan，是否降低证据等级、偷改范围/权威判断、引入第二套裁决，Task/DAG/Gate 是否完整。

Verdict：`PASS | REVISE | BLOCKED_EVIDENCE | BLOCKED_UNVERIFIED_REFERENCE | USER_APPROVAL_REQUIRED | CORE_PLAN_REVISION_REQUIRED`。
