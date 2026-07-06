# Multi-Agent Core Workflow

## 1. 主流程状态机

```text
INIT
  -> ENV_CHECK
  -> RESEARCH
  -> CATEGORY_DISCOVERY
  -> BATCH_PLAN_BY_CODEX_B
  -> WAVE_LOOP
  -> FINAL_REGRESSION
  -> FINAL_ACCEPTANCE_BY_CODEX_B
  -> OPTIONAL_FINAL_INDEPENDENT_REVIEW_BY_CODEX_C
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

编排后端由 `--orchestrator=` 参数选择。Codex 开发者和测试者的固定职责不受编排后端影响。

### 默认（`--orchestrator=codex`）— Codex 编排 + Codex 执行

#### Codex A 主编排

- 长期负责分类、调度、代理责任、状态恢复、返工升级和最终完成判断。
- 默认模型 `gpt-5.4`，只在判断、冲突、升级节点上消耗强推理预算。
- 决定类别依赖图、并行批次和集成顺序。

#### Codex B 计划 + 甲方验收

- 负责类别计划、验收标准、需求符合性验收和修复后复查。
- 默认模型 `gpt-5.4`；计划不够细、验收冲突或复杂漏项时升 `gpt-5.5`。

#### Codex C 独立技术审查

- 只在高风险、争议、连续失败或发布前启动。
- 默认模型 `gpt-5.4`；高风险或第二意见场景可升 `gpt-5.5`。

#### Claude provider 默认与升级

- 当前类别默认从 MiniMax provider 开始。
- 第一次返工失败后，主编排先看是 plan / standard / developer / tester 哪边的问题。
- 若确定 Claude 侧能力或额度不足：切到 DeepSeek V4。
- 若 MiniMax 额度不足：直接切 DeepSeek V4，不等第二次失败。

### `--orchestrator=reasonix` — Reasonix 编排 + Codex 执行

#### Reasonix 主编排

- 长期负责分类、调度、代理责任、状态恢复、返工升级和最终完成判断。
- 编排决策在 Reasonix 本会话内完成，固定使用 **deepseekV4pro** 模型。
- 决定类别依赖图、并行批次和集成顺序。
- Codex 只做执行，不参与编排决策。

#### Codex 开发者

- 负责类别实现、代码修改、自测。
- 模型：deepseekV4pro/flash **可选**（简单用 flash，复杂用 pro）。
- 由 Reasonix 编排按需拉起子会话。

#### Codex 测试者

- 负责类别测试、验收、修复后回归。
- 模型：固定使用 **deepseekV4flash**。
- 发现问题后验证到关闭。

## 4. 文件流转优先

主会话长期状态只认：

- `Git`
- `.collab-work/STATE.json`
- `.collab-work/ISSUES.json`
- `.collab-work/runs/<task-id>/<category-id>/manifest.json`
- `CURRENT_STATUS.md`
- `HANDOFF.md`
- `DECISIONS.md`
- `BUGS.md`

兼容性文件只在脚本仍依赖时同步：

- `.collab-work/ORCHESTRATOR_STATE.json`
- `.collab-work/AGENT_REGISTRY.json`
- `.collab-work/ISSUE_REGISTRY.json`

## 5. Research First

正式分类和计划前，默认先由 researcher 做机械性调研：

- 目录整理
- 文件定位
- 调用链梳理
- 当前行为归纳
- 测试文件定位
- 风险与未知项标记

研究结果必须区分：

- `CONFIRMED`
- `INFERRED`
- `UNKNOWN`

## 6. 受控并行

- 最大并行度为 3，但不强制凑满。
- 并行的是“不同类别”，不是同一类别内多个开发代理。
- 只有低耦合类别允许同批并行。
- 每个并行类别必须有独立 worktree、branch、developer 责任身份、tester 责任身份和类别目录。

不允许直接并行的典型情况：

- 共享数据库结构
- 共享核心状态
- 共享关键文件
- 接口仍在变化
- 一个类别输出是另一个类别输入

## 5. 返工闭环

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
- **第一次返工失败就检查问题出在哪。**
- 同一问题最多自动进行两轮相似修复；第二次仍失败必须升级假设、模型、证据或会话。

## 6. 主编排介入节点

出现以下情况时，编排者必须介入：

- 第一次返工后仍未通过
- plan、review、test 标准明显不一致
- developer 连续给出相似错误方案
- 模型额度不足或明显能力不够

介入流程根据编排后端区分：

### 默认（`--orchestrator=codex`）

Codex A 执行：

```text
REWORK_FAIL_ONCE
  -> ORCHESTRATOR_DIAGNOSE
  -> CLASSIFY_CAUSE
  -> OPTIONAL_BRAINSTORM
  -> OPTIONAL_WRITING
  -> UPGRADE_RIGHT_AGENT_OR_MODEL
  -> RESUME_ORIGINAL_OWNER
```

### `--orchestrator=reasonix`

Reasonix 编排者执行：

1. **第一轮返工不通过**：自查归因（`RESEARCH_GAP` / `PLAN_GAP` / `DEVELOPER_EXECUTION` / `TEST_SYSTEM_ISSUE` / `ENVIRONMENT_LIMIT`），记录改进项
2. **第二轮仍不通过**：
   - 开发者问题：升级 Codex 从 flash 到 pro，或切换子会话
   - 编排者自身能力不足：通过 `<<<NEEDS_PRO>>>` 在当前会话内升级
   - 环境问题：记录并绕过

## 7. 先易后难

- 当前类别先解决低耦合、可稳定收敛的问题。
- 复杂问题可 `SKIPPED_DEFER_NEXT_TIER`，先完成其他可解项。
- 最后再统一升级模型、tier 或独立审查处理复杂项。

## 8. 集成波次

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
- 双类冲突查两类文档并由 Codex A 决定接口/顺序
- 真正三方问题才加载三类文档

## 9. 完成前验证

类别关闭前必须保留新鲜验证证据：

- `VERIFIED_COMMIT`
- `VERIFICATION_COMMAND`
- `VERIFICATION_TIME`
- `EXIT_CODE`
- `RESULT_FILE`
- `DEVICE_TEST_STATUS`
- `REMAINING_RISKS`
