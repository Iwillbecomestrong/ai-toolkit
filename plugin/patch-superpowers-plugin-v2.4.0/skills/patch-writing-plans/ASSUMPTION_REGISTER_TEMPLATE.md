# Assumption Register

## Rules

- `LOAD_BEARING`：若为假，会让核心功能失效、改变公共接口/状态所有权/Task DAG/验收预期，或导致多个 Task 一起返工。
- 存在 `LOAD_BEARING + UNKNOWN/INCONCLUSIVE` 时，禁止冻结核心计划和生成详细计划。

| ID | Statement | Type | Status | Risk if False | Required Evidence Level | Evidence Artifact | Validation Experiment |
|---|---|---|---|---|---|---|---|
| A-01 | | `LOAD_BEARING | LOCAL` | `UNKNOWN | VALIDATED | FALSIFIED | INCONCLUSIVE` | | | | |
