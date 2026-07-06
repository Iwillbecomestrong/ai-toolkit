# Multi-Agent Core Routing

## 1. 所有者路由

| 问题类型 | 默认 owner | 复查 owner | 处理方式 |
|---|---|---|---|
| 代码调研不足、调用链未查清、文件范围不准 | 原 researcher | 主编排 | 先补调研，再决定是否升级到第二调研代理或 Codex A |
| 产品逻辑错误、崩溃、状态机/生命周期缺陷 | 原 developer | 发现者 | developer 修产品代码 |
| 验收指出漏做、少做、做偏 | 原 developer | Codex B | developer 修后，Codex B 复查 |
| 独立技术审查指出架构/安全风险 | 原 developer | Codex C | developer 修后，必要时再审 |
| 单元测试断言、夹具、mock、测试数据错误 | 原 tester | 原 tester | tester 修测试系统，不改产品代码 |
| 测试覆盖不足 | 原 tester | 原 tester | tester 补测，若暴露产品 bug 再转 developer |
| 计划摘要、交接说明、审查输入不清 | writing | 主编排 | writing 重写说明，不改产品代码 |
| 返工反复但根因不清 | brainstorm | 主编排 | brainstorm 诊断，不改产品代码 |

## 2. 第一次返工失败后的判断

先区分：

1. `PLAN_GAP`
2. `STANDARD_MISMATCH`
3. `DEVELOPER_EXECUTION`
4. `TEST_SYSTEM_FAILURE`
5. `ENVIRONMENT_LIMIT`

如果第一次返工不通过，主编排必须先归因，再决定升级谁。升级路径按编排后端区分：

### 默认（`--orchestrator=codex`）
- researcher 问题：先恢复原 researcher 补充；仍不足则第二调研代理交叉验证；再不行才由 Codex A 定向阅读关键代码
- plan / acceptance / review 问题：升级 Codex 到 `gpt-5.5`
- developer / tester 问题：升级当前类别 Claude provider 到 DeepSeek V4
- MiniMax 额度不足：直接切 DeepSeek V4

### `--orchestrator=reasonix`
- researcher 问题：先恢复原 researcher；仍不足则第二调研代理交叉验证；再不行由 Reasonix 编排直读关键代码
- developer 问题：升级 Codex 开发者从 flash 到 pro，或换子会话
- tester 问题：确认 tester 模型（deepseekV4flash 已固定）；若仍不够，轮到 pro developer 做验收补充
- 编排者自身能力不足：通过 `<<<NEEDS_PRO>>>` 在当前会话内升级

## 3. 聚合返工

同一类别、同一轮、同一 owner 的问题先聚合再返工。

## 4. 并行与集成问题

不同类别并行时：

- 每类必须有独立 worktree 和 branch
- 集成失败先看失败测试、日志、冲突文件和修改文件清单
- 单类问题只回单类原 owner
- 双类冲突由编排者（Codex A 或 Reasonix）确定接口或合并顺序，再交回对应原 owner
- 真正三方问题才升级成 wave 级问题

## 5. 先易后难

- 容易解决的先做完。
- 复杂项可标 `SKIPPED_DEFER_NEXT_TIER`。
- 不要让一个复杂问题阻塞整类所有简单问题。

## 6. 相似返工上限

- 同一问题最多自动进行两轮相似修复。
- 第二次仍失败时，必须补证据、换假设、升级模型或更换会话。
- 不得无限试错。
