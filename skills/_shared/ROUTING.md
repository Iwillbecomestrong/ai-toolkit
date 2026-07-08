# Shared Routing — auto-dev / multi-agent-core

## 1. 所有者路由

| 问题类型 | 默认 owner | 复查 owner | 处理方式 |
|---|---|---|---|
| 代码调研不足、调用链未查清、文件范围不准 | 原 researcher | 主编排 | 先补调研 → 第二调研代理交叉验证 → 主编排直读关键代码 |
| 产品逻辑错误、崩溃、状态机/生命周期缺陷 | 原 developer | 发现者 | developer 修产品代码 |
| 验收指出漏做、少做、做偏 | 原 developer | 验收代理 | developer 修后，验收代理复查 |
| 独立技术审查指出架构/安全风险 | 原 developer | 审查代理 | developer 修后，必要时再审 |
| 单元测试断言、夹具、mock、测试数据错误 | 原 tester | 原 tester | tester 修测试系统，不改产品代码 |
| 测试覆盖不足 | 原 tester | 原 tester | tester 补测，若暴露产品 bug 再转 developer |
| 设备/环境相关问题 | 原 tester | 主编排 | 修测试环境或脚本；设备暂不可用则写入 `REAL_DEVICE_PLAN.md` |
| 计划摘要、交接说明、审查输入不清 | writing | 主编排 | writing 重写说明，不改产品代码 |
| 返工反复但根因不清 | brainstorm | 主编排 | brainstorm 诊断，不改产品代码 |
| 高风险专项验证失败 | 原 developer（通常） | 发现者 | 立即停下修复，不带病继续堆功能 |

## 2. 第一次返工失败后的判断

先区分归因：

1. `RESEARCH_GAP` — 调研不充分
2. `PLAN_GAP` — 计划有缺陷
3. `STANDARD_MISMATCH` — 验收/审查标准不一致
4. `DEVELOPER_EXECUTION` — 开发者实现问题
5. `TEST_SYSTEM_ISSUE` — 测试系统/环境问题
6. `ENVIRONMENT_LIMIT` — 环境限制（设备不可用等）

如果第一次返工不通过，主编排必须先归因，再决定升级谁：

- **researcher 问题**：先恢复原 researcher 补充；仍不足则第二调研代理交叉验证；再不行由主编排直读关键代码
- **plan 问题**：让 DeepSeek V4 Pro planner 修订计划（触发 `plan_must_be_agent`），提供更具体的反馈；修订后交 Codex 复审
- **developer 问题**：升级开发者模型（flash → pro），或换子会话
- **tester 问题**：确认测试逻辑；若 tester 能力不足，由 pro developer 做验收补充
- **编排者自身能力不足**：升级模型或通过标记升级

## 3. 聚合返工

同一类别、同一轮、同一 owner 的问题先聚合再返工。

## 4. 并行与集成问题

不同类别并行时：

- 每类必须有独立 worktree 和 branch
- 集成失败先看失败测试、日志、冲突文件和修改文件清单
- 单类问题只回单类原 owner
- 双类冲突由主编排确定接口或合并顺序，再交回对应原 owner
- 真正三方问题才升级成 wave 级问题

## 5. 先易后难

- 容易解决的先做完。
- 复杂项可标 `SKIPPED_DEFER_NEXT_TIER`。
- 不要让一个复杂问题阻塞整类所有简单问题。

## 6. 相似返工上限

- 同一问题最多自动进行两轮相似修复。
- 第二次仍失败时，必须补证据、换假设、升级模型或更换会话。
- 不得无限试错。（`max_retry_gate` 钩子强制执行）
