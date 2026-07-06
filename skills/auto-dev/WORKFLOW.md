# Auto Dev Workflow

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

## 2. 三个 Codex 对话 + Claude 编排

**强模型优先配置顺序**：Codex B（计划 + 甲方验收）> Codex C（高风险独立审查）> Codex A（仅 `--orchestrator=codex` 模式下、第二轮返工仍不通过时短期辅助）。Codex B / C 的固定职责不受编排后端选择影响。

### Claude 主编排（默认）

- 长期负责分类、调度、代理责任、状态恢复、返工升级和最终完成判断。
- 编排决策在本会话（Claude）内完成；机械活（路径转发、状态维护、代理恢复、普通合并）默认消耗 Claude provider（MiniMax → DeepSeek V4）。
- 决定类别依赖图、并行批次和集成顺序。

### Codex A 编排辅助（仅 `--orchestrator=codex`）

- 启动参数含 `--orchestrator=codex` 时启用，由 Claude 编排按需通过 `Agent(agent_type='codex:codex-rescue')` 拉起短期会话。
- **触发条件**：第二轮返工仍不通过（第一轮始终由 Claude 编排自查归因 + 记录改进项）；用于首次返工归因深度化、跨类冲突仲裁、模型升级决策这 3 类升级判断节点。
- 默认模型 `gpt-5.4`；只在被调用时消耗强推理预算，不长期持有项目上下文。

### Codex B 计划 + 甲方验收（强模型优先）

- 负责类别计划、验收标准、需求符合性验收和修复后复查。
- 默认模型 `gpt-5.4`；计划不够细、验收冲突或复杂漏项时升 `gpt-5.5`。

### Codex C 独立技术审查（强模型次优先）

- 只在高风险、争议、连续失败或发布前启动。
- 默认模型 `gpt-5.4`；高风险或第二意见场景可升 `gpt-5.5`。

## 3. Claude provider 默认与升级

- 当前类别默认从 MiniMax provider 开始。
- 第一次返工失败后，主编排先看是 plan / standard / developer / tester 哪边的问题。
- 若确定 Claude 侧能力或额度不足：切到 DeepSeek V4。
- 若 MiniMax 额度不足：直接切 DeepSeek V4，不等第二次失败。

## 4. 文件流转优先

主会话长期状态只认：

- `Git`
- `.ai-work/STATE.json`
- `.ai-work/ISSUES.json`
- `.ai-work/runs/<task-id>/<category-id>/manifest.json`
- `CURRENT_STATUS.md`
- `HANDOFF.md`
- `DECISIONS.md`
- `BUGS.md`

兼容性文件只在脚本仍依赖时同步：

- `.ai-work/ORCHESTRATOR_STATE.json`
- `.ai-work/AGENT_REGISTRY.json`
- `.ai-work/ISSUE_REGISTRY.json`

## 5. Research First

正式分类和计划前，默认先由 researcher 做机械性调研：

- 目录整理
- 文件定位
- 调用链梳理
- 当前行为归纳
- Android 测试文件、ADB / emulator 脚本、日志路径定位
- 风险与未知项标记

研究结果必须区分：

- `CONFIRMED`
- `INFERRED`
- `UNKNOWN`

## 6. 受控并行

- 最大并行度为 3，但不强制凑满。
- 并行的是“不同类别”，不是同一类别内多个开发代理。
- 只有低耦合类别允许同批并行。
- 每个并行类别必须有独立 worktree、branch、developer 责任身份、tester 责任身份、必要时 emulator tester 责任身份和类别目录。

不允许直接并行的典型情况：

- 共享数据库结构
- 共享核心状态
- 共享关键文件
- 接口仍在变化
- 一个类别输出是另一个类别输入
- 多个类别同时修改跨日、后台服务、无障碍或核心锁定链路

## 7. 返工闭环

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

## 8. 主编排介入节点

出现以下情况时，Claude 编排必须介入：

- 第一次返工后仍未通过
- plan、review、test 标准明显不一致
- developer 连续给出相似错误方案
- MiniMax 额度不足或明显能力不够

**两级升级路径**：

1. **第一轮返工不通过**：Claude 编排自查归因，区分 `RESEARCH_GAP` / `PLAN_GAP` / `STANDARD_MISMATCH` / `DEVELOPER_EXECUTION` / `TEST_SYSTEM_ISSUE` / `ENVIRONMENT_LIMIT`，并将根因**记录为改进项**：
   - 流程改进：更新 `WORKFLOW.md` / `ROUTING.md` / 对应 skill 文件
   - 记忆改进：写入项目 memory（`.claude/projects/.../memory/`）
2. **第二轮返工仍不通过**：
   - 默认模式：Claude 编排重判 + 升级 Claude provider（MiniMax → DeepSeek V4）
   - `--orchestrator=codex` 模式：调用 Codex A 短期会话辅助（首次返工归因深度化、跨类冲突仲裁、模型升级决策），Claude 整合后执行

## 9. 先易后难

- 当前类别先解决低耦合、可稳定收敛的问题。
- 复杂问题可 `SKIPPED_DEFER_NEXT_TIER`，先完成其他可解项。
- 最后再统一升级模型、tier 或独立审查处理复杂项。

## 10. 集成波次

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
- 双类冲突查两类文档并由 Claude 编排决定接口/顺序；第二轮仍冲突时，`--orchestrator=codex` 模式可调 Codex A 辅助判断
- 真正三方问题才加载三类文档

## 11. 完成前验证

类别关闭前必须保留新鲜验证证据：

- `VERIFIED_COMMIT`
- `VERIFICATION_COMMAND`
- `VERIFICATION_TIME`
- `EXIT_CODE`
- `RESULT_FILE`
- `DEVICE_TEST_STATUS`
- `REMAINING_RISKS`
