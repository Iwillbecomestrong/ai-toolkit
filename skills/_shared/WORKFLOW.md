# Shared Workflow — auto-dev / multi-agent-core

## 1. 主流程状态机

```text
INIT
  -> ENV_CHECK
  -> RESEARCH
  -> CATEGORY_DISCOVERY
  -> BATCH_PLAN_BY_SUBAGENT   ← plan_must_be_codex 钩子
  -> WAVE_LOOP
  -> FINAL_REGRESSION
  -> FINAL_ACCEPTANCE
  -> OPTIONAL_FINAL_INDEPENDENT_REVIEW
  -> COMPLETE
```

`WAVE_LOOP` 展开为：

```text
WAVE_PREPARE
  -> START_UP_TO_3_CATEGORIES
  -> CATEGORY_LOOP (parallel where allowed)
  -> WAVE_INTEGRATION
  -> WAVE_CLOSE
```

`CATEGORY_LOOP` 展开为：

```text
CATEGORY_START
  -> IMPLEMENT_LOOP
  -> CATEGORY_TEST
  -> CATEGORY_ACCEPTANCE
  -> OPTIONAL_CATEGORY_INDEPENDENT_REVIEW
  -> CATEGORY_CLOSE
```

## 2. 编排后端与角色模型

编排后端由各 SKILL.md 的 `--orchestrator=` 参数选择。子代理（开发者/测试者）的固定职责不受编排后端影响。

### 通用角色

| 角色 | 职责 |
|---|---|
| 主编排者 | 分类、调度、代理责任、状态恢复、返工升级、最终完成判断 |
| 开发者（子代理） | 类别实现、代码修改、自测 |
| 测试者（子代理） | 类别测试、验收、修复后回归 |
| 调研代理 | 目录整理、文件定位、调用链梳理、当前行为归纳 |
| 计划代理（子代理） | 类别计划、验收标准 — **必须由子代理生成 PLAN.md** |

### 编排后端差异

各后端的具体模型分配参见各自 SKILL.md：
- **Claude 编排** → `auto-dev` SKILL.md
- **Codex 编排** → `multi-agent-core` SKILL.md（默认）
- **Reasonix 编排** → `multi-agent-core` SKILL.md（`--orchestrator=reasonix`）

## 3. 文件流转

主会话长期状态只认：

- `Git`
- `{STATE_DIR}/STATE.json`
- `{STATE_DIR}/ISSUES.json`
- `{STATE_DIR}/runs/<task-id>/<category-id>/manifest.json`
- `CURRENT_STATUS.md`
- `HANDOFF.md`
- `DECISIONS.md`
- `BUGS.md`

> `{STATE_DIR}` 由各自 SKILL.md 定义：auto-dev 使用 `.ai-work`，multi-agent-core 使用 `.collab-work`。

## 4. Research First

正式分类和计划前，默认先由调研代理做机械性调研：

- 目录整理
- 文件定位
- 调用链梳理
- 当前行为归纳
- 测试文件、日志路径定位
- 风险与未知项标记

研究结果必须区分：`CONFIRMED` / `INFERRED` / `UNKNOWN`

## 5. 受控并行

- 最大并行度为 3，但不强制凑满。
- 并行的是"不同类别"，不是同一类别内多个开发代理。
- 只有低耦合类别允许同批并行。
- 每个并行类别必须有独立 worktree、branch、developer 责任身份、tester 责任身份和类别目录。

不允许直接并行的典型情况：

- 共享数据库结构
- 共享核心状态
- 共享关键文件
- 接口仍在变化
- 一个类别输出是另一个类别输入
- 多个类别同时修改跨日、后台服务或核心锁定链路

启动并行前 → 触发 `parallel_safety_check` 钩子。

## 6. 返工闭环

```text
TEST_FAIL or ACCEPTANCE_FAIL or INDEPENDENT_REVIEW_FAIL
  -> AGGREGATE_ISSUES
  -> ORCHESTRATOR_CHECK_CAUSE
  -> ROUTE_TO_OWNER
  -> REPAIR
  -> RETEST_AFFECTED_CATEGORY
  -> RECHECK_BY_DISCOVERER
```

规则：

- 谁开发谁修改。
- 谁发现谁验证到关闭。
- 审查和测试代理默认不改生产代码。
- 第一次返工失败就检查问题出在哪。
- 同一问题最多自动两轮相似修复；第 3 轮 → 触发 `max_retry_gate` 钩子。

## 7. 主编排介入节点

出现以下情况时，编排者必须介入：

- 第一次返工后仍未通过
- plan、review、test 标准明显不一致
- developer 连续给出相似错误方案
- 模型额度不足或明显能力不够

介入流程：

```text
REWORK_FAIL_ONCE
  -> ORCHESTRATOR_DIAGNOSE
  -> CLASSIFY_CAUSE (RESEARCH_GAP / PLAN_GAP / STANDARD_MISMATCH / DEVELOPER_EXECUTION / TEST_SYSTEM_ISSUE / ENVIRONMENT_LIMIT)
  -> 记录改进项（更新 WORKFLOW/ROUTING + 项目 memory）
  -> UPGRADE_RIGHT_AGENT_OR_MODEL
  -> RESUME_ORIGINAL_OWNER
```

## 8. 先易后难

- 当前类别先解决低耦合、可稳定收敛的问题。
- 复杂问题可 `SKIPPED_DEFER_NEXT_TIER`，先完成其他可解项。
- 最后再统一升级模型处理复杂项。

## 9. 集成波次

每个 wave 的标准流程：

```text
WAVE_PREPARE
  -> create isolated worktrees
  -> run up to 3 categories
  -> create integration worktree
  -> merge in planned order
  -> quick integration check after each merge
  -> wave integration test
```

集成问题处理：

- 单类问题查单类文档并交回原开发代理
- 双类冲突查两类文档并由主编排决定接口/顺序
- 真正三方问题才加载三类文档

## 10. 完成前验证

类别关闭前必须保留新鲜验证证据：

- `VERIFIED_COMMIT`
- `VERIFICATION_COMMAND`
- `VERIFICATION_TIME`
- `EXIT_CODE`
- `RESULT_FILE`
- `DEVICE_TEST_STATUS`
- `REMAINING_RISKS`

提交前 → 触发 `pre_commit_gate` 钩子。

任务完成后 → 触发 `post_task_reflection` 钩子。
