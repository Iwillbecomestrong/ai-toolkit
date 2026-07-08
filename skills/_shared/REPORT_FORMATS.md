# Shared Report Formats — auto-dev / multi-agent-core

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

> **codex_output_visible 钩子**：Codex 子代理的结构化返回必须展示在主编排者输出中，不得静默丢弃。

## 2. 状态目录关键文件

> `{STATE_DIR}` = `.ai-work`（auto-dev）或 `.collab-work`（multi-agent-core）

### `STATE.json`

主编排全局状态源。记录：当前任务、当前波次、当前类别、当前阶段、下一代理、下一输入文件、风险、最近 commit。

### `manifest.json`

类别状态源。记录：`worktree`、`branch`、`owner_ids`、`sessions`、`plan_version`、`open_issues`、`category_status`、`latest_commit`、`verification`。

### `ISSUES.json`

记录：`issue_id`、`category_id`、`description`、`discovered_by`、`fix_owner`、`verify_owner`、`status`、`evidence_file`、`fix_file`、`verify_file`、`related_commit`。

### 兼容性文件

- `ORCHESTRATOR_STATE.json`
- `AGENT_REGISTRY.json`
- `ISSUE_REGISTRY.json`
- `waves/wave-<n>/INTEGRATION_STATE.json`

## 3. 任务目录文件

### `CODE_CONTEXT.md`

- `user_goal`、`current_behavior`、`related_files`、`call_chain`
- `state_and_data`、`existing_tests`、`risks`、`unknowns`、`verification_points`

所有结论标记为 `CONFIRMED` / `INFERRED` / `UNKNOWN`。

### `PLAN.md`

计划代理（DeepSeek V4 Pro planner / OpenCode-OMO hyperplan）生成。开发代理首次进入、计划实质变化或新会话接手时，必须完整阅读，不得用摘要替代。（`plan_must_be_agent` 钩子强制执行）

### `STATUS.md`

- `task_id`、`current_stage`、`base_commit`、`repair_cycle`、`max_repair_cycles`
- `current_category`、`completed_categories`、`pending_categories`
- `current_tier`、`final_decision`

### `CURRENT_STATUS.md`

- `current_category`、`category_goal`、`completed_items`
- `remaining_items`、`current_owner`、`current_blockers`、`next_action`

### `HANDOFF.md`

- `from_stage`、`to_stage`、`current_category`
- `resolved_in_this_round`、`open_issues`
- `evidence_paths`、`current_tier_provider`、`next_required_action`

### `BUGS.md`

每个问题至少包含：`issue_id`、`category_id`、`discovered_by`、`fix_owner`、`verify_owner`、`status`、`summary`、`evidence_file`、`related_commit`。

### `TEST_REPORT.md`

必须显式标记：

- `compile_passed: true/false`
- `functional_test_passed: true/false`
- `verified_commit`、`verification_command`、`verification_time`
- `exit_code`、`result_file`
- `device_test_status`、`remaining_risks`

### `REVIEW_REPORT.md`

第一行必须是：`DECISION: APPROVE | APPROVE_WITH_NOTES | REQUEST_CHANGES`

注明：`reviewer_role: acceptance | independent`、`review_scope: category | final`

### `AUTO_DEV_LEARNINGS.md`

任务完成后的沉淀文件（`post_task_reflection` 钩子）。记录：踩坑、有效命令、测试方法、值得加入 Skill 的规则。
