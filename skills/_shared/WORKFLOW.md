# Shared Workflow — auto-dev / multi-agent-core

## 1. 主流程状态机

```text
INIT
  -> ENV_CHECK
  -> RESEARCH
  -> CATEGORY_DISCOVERY          ← 主编排者亲自分类，严禁委托 Codex
  -> BATCH_PLAN_BY_SUBAGENT      ← 每类独立启动一个 Codex planner（N 类 = N 次 Codex 调用）
  -> WAVE_LOOP
  -> FINAL_REGRESSION
  -> FINAL_ACCEPTANCE
  -> OPTIONAL_FINAL_INDEPENDENT_REVIEW
  -> COMPLETE
```

### CATEGORY_DISCOVERY（主编排者亲自执行，不可委托）

1. 主编排者基于 RESEARCH 阶段的产物（CODE_CONTEXT.md、调研报告），**亲自**阅读并理解每个 Bug/需求的代码范围
2. 按**文件耦合度**分组：改同一文件/同一模块的归入同一类
3. 识别依赖关系：A 类的输出是否是 B 类的输入
4. 产出 `CATEGORIES.md`，至少包含：
   - 每个类覆盖哪些 Bug/需求
   - 涉及哪些文件
   - 类之间的依赖关系（无依赖 / A→C / 共享文件冲突）
   - 推荐执行顺序和可并行组合
5. **严禁**将分类工作丢给 Codex 子代理。分类是编排决策，不是机械劳动

### BATCH_PLAN_BY_SUBAGENT（每类独立 Codex planner）

1. 对 CATEGORIES.md 中的**每个类别**，独立启动一个 Codex planner 子代理
2. N 个类别 = N 次 Codex planner 调用（可以部分并行，因为各类独立）
3. 每个 Codex planner 只看到自己类别的需求、涉及文件、约束条件
4. 每个类别产出独立的 `PLAN.md` + `plan.meta.json`
5. 主编排者逐个 review 每类计划，检查跨类接口一致性，批准后进入 WAVE_LOOP
6. **严禁**一个 Codex planner 包揽所有类别的计划（会导致上下文污染、计划质量下降）

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

## 11. 工作树 commit 规范（强约束）

**目的**：防止 Agent 在 working tree 累积未提交改动 → linter/编辑器/session 中断时全丢（实测 100+ 行代码丢失事件）。

### `commit_step_gate`（每步强制）

任何源码/文档修改后，**必须**在同一 Agent 的下一步操作前：

```bash
git status --short                       # 确认本次修改范围
git add <精确文件>                       # 不要用 git add . / git add -A
git commit -m "<明确的 step message>"
```

**禁止**：
- 把多个步骤累积到 working tree 再一次性 commit
- 用 `git add .` / `git add -A`（会带进无关文件）
- "等真机验收再 commit"（真机前要 commit，否则丢失无恢复）

### `working_tree_audit`（任务/Agent 切换时强制）

Agent 退出、任务完成、子任务切换前**必须**：

```bash
git status --short                       # 输出必须为空，否则 commit 或 revert
```

**失败行为**：
- 任务结束 `git status` 不为空 → 不得声称"完成"
- Agent 报"已完成"但 `git log --oneline` 没有新 commit → 主编排必须强制重做或 commit

### 实施保障

- `scripts/auto_dev_guard.py` Gate 5: commit/push 前自动检查
- `auto-dev/SKILL.md` §commit_step_gate: 提示词层强制
- `auto-code-android-dev/SKILL.md` §android_commit_step_gate: Android 额外加编译验证
