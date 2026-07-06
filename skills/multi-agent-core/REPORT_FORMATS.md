# Multi-Agent Core Report Formats

## 1. 结构化短返回

所有子代理完成当前动作后，只向主会话返回：

```text
STATUS: PASS | FAIL | BLOCKED
OUTPUT_FILE: <detailed output file path>
SUMMARY: <1-3 句话摘要>
CONFIDENCE: HIGH | MEDIUM | LOW
RISK: LOW | MEDIUM | HIGH
COMMIT: <git commit or NONE>
AGENT_ROLE: researcher | planner | developer | tester | acceptance | independent-review | brainstorm | writing
AGENT_SESSION: <session id or agent id or UNKNOWN>
NEXT_AGENT: <role or NONE>
NEXT_INPUT: <path or NONE>
```

## 2. `.collab-work` 关键文件

### `STATE.json`

主编排全局状态源。记录：

- 当前任务
- 当前波次
- 当前类别
- 当前阶段
- 下一代理
- 下一输入文件
- 风险
- 最近 commit

### `manifest.json`

类别状态源。记录：

- `worktree`
- `branch`
- `owner_ids`
- `sessions`
- `plan_version`
- `open_issues`
- `category_status`
- `latest_commit`
- `verification`

### `ISSUES.json`

记录：

- `issue_id`
- `category_id`
- `description`
- `discovered_by`
- `fix_owner`
- `verify_owner`
- `status`
- `evidence_file`
- `fix_file`
- `verify_file`
- `related_commit`

### 兼容性文件

如果现有脚本仍依赖，可同步维护：

- `ORCHESTRATOR_STATE.json`
- `AGENT_REGISTRY.json`
- `ISSUE_REGISTRY.json`
- `waves/wave-<n>/INTEGRATION_STATE.json`

### `waves/wave-<n>/INTEGRATION_STATE.json`

记录：

- `wave`
- `categories`
- `merge_order`
- `merged`
- `current_category`
- `integration_status`
- `failed_test`
- `related_files`
- `next_action`

### `manifest.json`

记录：当前类别输入文件、输出文件、worktree、branch 和 owner 映射。

## 3. 任务目录文件

### `CODE_CONTEXT.md`

- `user_goal`
- `current_behavior`
- `related_files`
- `call_chain`
- `state_and_data`
- `existing_tests`
- `risks`
- `unknowns`
- `verification_points`

所有结论应标记为 `CONFIRMED` / `INFERRED` / `UNKNOWN`。

### `STATUS.md`

- `task_id`
- `current_stage`
- `base_commit`
- `repair_cycle`
- `max_repair_cycles`
- `current_category`
- `completed_categories`
- `pending_categories`
- `current_tier`
- `final_decision`

### `CURRENT_STATUS.md`

- `current_category`
- `category_goal`
- `completed_items`
- `remaining_items`
- `current_owner`
- `current_blockers`
- `next_action`

### `HANDOFF.md`

- `from_stage`
- `to_stage`
- `current_category`
- `resolved_in_this_round`
- `open_issues`
- `evidence_paths`
- `current_tier_provider`
- `next_required_action`

### `BUGS.md`

每个问题至少包含：

- `issue_id`
- `category_id`
- `discovered_by`
- `fix_owner`
- `verify_owner`
- `status`
- `summary`
- `evidence_file`
- `related_commit`

### `TEST_REPORT.md`

必须显式标记：

- `compile_passed: true/false`
- `functional_test_passed: true/false`
- `verified_commit`
- `verification_command`
- `verification_time`
- `exit_code`
- `result_file`
- `device_test_status`
- `remaining_risks`

### `REVIEW_REPORT.md`

第一行必须是：

```text
DECISION: APPROVE | APPROVE_WITH_NOTES | REQUEST_CHANGES
```

并注明：

- `reviewer_role: acceptance | independent`
- `review_scope: category | final`
