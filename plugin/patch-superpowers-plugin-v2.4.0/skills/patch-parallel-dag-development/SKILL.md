---
name: patch-parallel-dag-development
description: Use when a software task should be orchestrated with classified inputs, two-stage Sol planning, Claude implementation and plan challenge, Codex Luna review, and a dynamic Execution Task DAG.
---

# Patch Parallel DAG Development

## 角色

Claude 插件 Agents：`patch-investigator`、`patch-plan-challenger`、`patch-tdd-implementer`、`patch-integration-operator`。Sol/Luna 不是 Claude Agents，而由 `${CLAUDE_PLUGIN_ROOT}/bin/patch-superpowers-codex-workflow.py` 按 `config/model-routing.json` 调用。

## 主流程

```text
PATCH_BRAINSTORMING
→ INPUT_CLASSIFICATION
→ MUST_FOLLOW_READ
→ CLAUDE_INVESTIGATION
→ SOL_INDEPENDENT_CORE_PLAN
→ [必要时 REFERENCE_ACCESS_REQUIRED → 定点读取 → 声明验证]
→ CLAUDE_CORE_PLAN_CHALLENGE
→ WAITING_CORE_PLAN_APPROVAL
→ SOL_DETAILED_PLAN_SAME_THREAD
→ CLAUDE_DETAILED_PLAN_REVIEW
→ WAITING_EXECUTION_PLAN_APPROVAL
→ DAG_EXECUTION
→ FINAL_VERIFICATION
→ SOL_FINAL_AUDIT
→ USER_ACCEPTANCE
```

## 输入规则

- MUST_FOLLOW 必须完整读取并逐项覆盖。
- CONFIRMED_FACTS 只能来自证据。
- UNKNOWN 中承重项未关闭时不得冻结计划。
- REFERENCE_ONLY_PATHS 默认 NOT_READ；先从代码与调查独立推导。只有无法形成方案时才申请读取，技术声明必须验证真伪。

## 执行规则

Execution Task 可并行；Task 内 Steps 串行。Claude Work Pool 5，Luna Review Pool 5。独立 Integration Gate 可并行，protected dev 准入串行。Task 运行后不因长尾拆分。

同一业务事实只有一个权威判断，下游复用。修改权威判断必须告知用户并获明确批准。
