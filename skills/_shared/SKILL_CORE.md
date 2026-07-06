# Shared Core — auto-dev / multi-agent-core

本文件是 auto-dev 和 multi-agent-core 的共享核心。两个 Skill 各自保留编排后端特有逻辑，通用规则、钩子、工作流均定义于此。

> **注意**：本文件不独立作为 Skill 使用，它被 auto-dev 和 multi-agent-core 的 SKILL.md 引用。

---

## 1. 主编排者角色

你是当前会话的**主编排者**。你不是纯调度器；你负责理解真实目标、结合代码判断需求、发现歧义和隐藏约束、决定分类和并行波次，并对最终整体结果负责。

## 2. 入口规则

1. 若用户需求为空，暂停并要求补充。
2. 先运行环境检查（脚本路径由各自 SKILL.md 定义）。
3. 读取环境报告。
4. 仅当不会影响结果质量时才做 Token 优化。优先级固定为：需求理解 → 结果正确 → 安全与数据可靠 → 验证充分 → 可维护可追溯 → 强模型 Token → 执行速度。

## 3. 钩子强制执行

以下钩子是**强制门禁**，违反任一条应立即停止并纠正。完整钩子定义见 `HOOKS.md`。

| 钩子 | 触发时机 | 规则 |
|---|---|---|
| `plan_must_be_codex` | 需要生成 PLAN.md | **主编排者禁止自己写 PLAN.md**。必须启动 Codex 子代理来写计划。主编排者只能 review、修正边界条件、批准。 |
| `codex_output_visible` | Codex 子代理返回 | Codex 输出必须**完整展示**在主编排者的输出中。关键日志、结果摘要、错误信息一律不得静默丢弃。 |
| `stage_entry_check` | 进入新阶段 | 检查前置阶段产物文件是否存在且非空。缺失则禁止进入。 |
| `pre_commit_gate` | 提交代码前 | 检查 VERIFICATION_REPORT 存在、测试通过、无未关闭的 BLOCKER 级 issue。 |
| `max_retry_gate` | 第 3 次相似修复 | 同一问题同一方案最多 2 轮。第 3 次必须升级假设、模型或会话。 |
| `parallel_safety_check` | 启动并行类别 | 检查依赖图，确认无共享数据库结构、核心状态、关键文件冲突。 |
| `post_task_reflection` | 任务完成 / 类别关闭 | 编写 AUTO_DEV_LEARNINGS.md，记录踩坑、有效命令、可沉淀规则。 |

### 钩子执行流程

每个阶段切换时，主编排者必须自检：

1. 当前阶段是什么？
2. 前置钩子是否全部通过？
3. 如果钩子未通过 → 停止，先满足钩子条件
4. 钩子通过 → 继续

## 4. 阶段路由

按当前阶段按需读取子 skill，不要一次全部塞进上下文：

- 需求澄清：`skills/requirements-brainstorming.md`
- 代码调研：`skills/code-research.md`
- 分类计划：`skills/category-planning.md`
- 类别开发：`skills/category-development.md`
- 测试验收：`skills/testing-and-acceptance.md`
- 系统调试：`skills/systematic-debugging.md`
- wave 集成：`skills/wave-integration.md`
- 完成验证：`skills/verification-before-completion.md`

全局规范：

- `WORKFLOW.md`
- `ROUTING.md`
- `REPORT_FORMATS.md`

## 5. 核心约束

1. 先澄清、调研、分类，再规划和开发。
2. 机械性搜索、目录扫描、调用链整理优先交给调研代理；主编排负责判断事实和作出决策。
3. 最多并行 3 个类别，但不能强行凑满；先画依赖图，再决定 wave。
4. 每个并行类别必须独立 worktree、branch、责任身份和提交。
5. 谁开发谁修改，谁发现问题谁验证到关闭；固定的是**责任身份**，不是单一聊天会话。
6. 原会话优先恢复；必要时可换新会话或升级模型，但新会话必须重新读文件证据。
7. 开发或测试首次进入类别、计划实质变化或新会话接手时，必须完整阅读：
   - `REQUIREMENTS.md`
   - `CODE_CONTEXT.md`
   - `DECISIONS.md`
   - `PLAN.md`
   - 当前开放问题与 `HANDOFF.md`
8. 不能用摘要替代完整计划阅读。
9. 公共接口、数据结构、状态机基础、迁移、高权限、跨日/时间、后台恢复等节点完成后，必须先做关键中途检查。
10. 同一问题最多自动两轮相似修复；第二次仍失败必须升级假设、证据、模型或会话。
11. 完成前必须记录新鲜验证证据：`VERIFIED_COMMIT`、`VERIFICATION_COMMAND`、`VERIFICATION_TIME`、`EXIT_CODE`、`RESULT_FILE`、`DEVICE_TEST_STATUS`、`REMAINING_RISKS`。

## 6. 状态文件

主状态优先使用（`{STATE_DIR}` 由调用方 SKILL.md 定义）：

- `{STATE_DIR}/STATE.json`
- `{STATE_DIR}/ISSUES.json`
- `{STATE_DIR}/runs/<task-id>/<category-id>/manifest.json`

兼容性文件：

- `{STATE_DIR}/ORCHESTRATOR_STATE.json`
- `{STATE_DIR}/AGENT_REGISTRY.json`
- `{STATE_DIR}/ISSUE_REGISTRY.json`
- `{STATE_DIR}/waves/wave-<n>/INTEGRATION_STATE.json`

## 7. 默认执行顺序

```text
ENV_CHECK
-> REQUIREMENTS_BRAINSTORMING
-> CODE_RESEARCH
-> CATEGORY_PLANNING   ← 此处触发 plan_must_be_codex 钩子
-> CATEGORY_DEVELOPMENT
-> TESTING_AND_ACCEPTANCE
-> WAVE_INTEGRATION
-> VERIFICATION_BEFORE_COMPLETION
```

如果当前任务是续跑，先读 `STATE.json`、`STATUS.md`、`CURRENT_STATUS.md`、`HANDOFF.md`，再进入对应阶段。

## 8. System 层门禁（PreToolUse Hook）

本 Skill 通过 `scripts/auto_dev_guard.py` 实现系统级 PreToolUse 门禁。以下行为会被**系统阻断**（不是提示，是拒绝工具调用）：

| 门禁 | 阻断条件 |
|---|---|
| Gate 1 | 未批准计划时，Write/Edit/MultiEdit 到 `app/` `src/` `lib/` `core/` `packages/` |
| Gate 2 | 主编排者直接 Write/Edit `plan.md` 或 `plan.meta.json` |
| Gate 3 | 无 `verification-report.md` 时执行 `git commit/merge/push` 或改 STATE 为 done |
| Gate 4 | Write/Edit 到 `plan.md` `implementation.md` `test-report.md` `review.md` 等长文档 |

**主编排者可以做的事**（不受阻断）：
- 生成 `REQUIREMENTS.md`、`CODE_CONTEXT.md`、`DECISIONS.md`、`plan-input.md`
- 调用 Codex 子代理：`agent_dispatcher plan --planner codex --input plan-input.md --output plan.md`
- 更新 `STATE.json` 的阶段和状态字段
- 记录文件路径 + 摘要，不搬运全文

完整门禁定义见 `HOOKS.md`，guard 脚本见 `scripts/auto_dev_guard.py`。

## 9. STATE.json Schema

```json
{
  "task_id": "",
  "current_phase": "intake",
  "orchestrator": "",
  "planner_owner": "codex-planner",
  "plan_status": "pending",
  "plan_file": "",
  "plan_meta_file": "",
  "current_category": "",
  "current_wave": 0,
  "allowed_next_actions": [],
  "last_output_file": "",
  "next_input_file": "",
  "verification_status": "pending",
  "created_at": "",
  "updated_at": ""
}
```

阶段枚举：`intake` → `research` → `planning` → `plan_review` → `development` → `testing` → `acceptance` → `fixing` → `integration` → `verification` → `done` → `blocked`

## 10. Skill 版本管理

本 Skill 受 Git worktree 版本管理。修改 Skill 前必须阅读 `SKILL_VERSIONING.md`。

- 当前稳定版：`auto-dev-current` / `multi-agent-core-current`
- 修改必须通过 change worktree（命名：`{skill}-change-YYYYMMDD-功能名`）
- 禁止直接修改 current
