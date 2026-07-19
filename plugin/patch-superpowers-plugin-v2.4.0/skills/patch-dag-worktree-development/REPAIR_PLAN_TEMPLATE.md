# Complex Repair Plan

## Metadata
- FAILURE_REPORT_PATH:
- FAILURE_REPORT_SHA256:
- REPAIR_BASE_COMMIT:
- CORE_PLAN_PATH:
- CORE_PLAN_APPROVAL_ID:
- ORIGINAL_PLAN_PATH:
- PLANNER_MODEL: gpt-5.6-sol
- REASONING_EFFORT: medium

## Root Cause and Repair Goal

## Single Business Fact Authority
- Facts involved:
- Existing authority:
- Repair reuses authority result: true | false
- Duplicate judgment introduced: false

若修复必须改变权威判断条件、结果语义、适用范围或消费者含义，停止本 Repair Plan，返回 `CORE_PLAN_REVISION_REQUIRED` 与 `USER_APPROVAL_REQUIRED`。

## Finding Disposition
| Failure/Finding | Root Cause | Action | Fix Task | Closing Evidence |
|---|---|---|---|---|

## Fix Task DAG

## Detailed Fix Tasks
每个 Fix Task 必须包含目标、依赖、精确写入范围、RED/GREEN/回归、真实行为证据、Codex Luna Review、提交和输出。

## Required Integration Gates

## Closure Contract
所有 Finding 必须明确 `CLOSED / STILL_OPEN / REGRESSED`，不能静默消失。
