# Auto Dev Routing

## 1. 所有者路由

| 问题类型 | 默认 owner | 复查 owner | 处理方式 |
|---|---|---|---|
| 代码调研不足、调用链未查清、文件范围不准 | 原 researcher | 主编排 | 先补调研 → 第二调研代理交叉验证 → Claude 编排直读关键代码；以上仍无解时，`--orchestrator=codex` 模式下可调 Codex A 定向阅读 |
| 产品逻辑错误、崩溃、状态机/生命周期缺陷 | 原 developer | 发现者 | developer 修产品代码 |
| 验收指出漏做、少做、做偏 | 原 developer | Codex B | developer 修后，Codex B 复查 |
| 独立技术审查指出架构/安全风险 | 原 developer | Codex C | developer 修后，必要时再审 |
| 单元测试断言、夹具、mock、测试数据错误 | 原 tester | 原 tester | tester 修测试系统，不改产品代码 |
| 测试覆盖不足 | 原 tester | 原 tester | tester 补测，若暴露产品 bug 再转 developer |
| AVD、ADB、安装、Logcat、模拟器自动化问题 | 原 emulator tester | 原 emulator tester | 修测试环境或脚本 |
| 模拟器或真机暴露产品错误 | 原 developer | 原 emulator tester | developer 修后，原设备测试者重测 |
| 设备暂不可用 | tester / emulator tester | 主编排 | 写入 `REAL_DEVICE_PLAN.md`，继续离线工作 |
| 计划摘要、交接说明、审查输入不清 | writing | 主编排 | writing 重写说明，不改产品代码 |
| 返工反复但根因不清 | brainstorm | 主编排 | brainstorm 诊断，不改产品代码 |
| 高风险专项验证失败 | 原 developer（通常） | 发现者 | 立即停下修复，不带病继续堆功能 |

## 2. 第一次返工失败后的判断

先区分：

1. `RESEARCH_GAP`
2. `PLAN_GAP`
3. `STANDARD_MISMATCH`
4. `DEVELOPER_EXECUTION`
5. `TEST_SYSTEM_ISSUE`
6. `ENVIRONMENT_LIMIT`

如果第一次返工不通过，主编排必须先归因，再决定升级谁：

- researcher 问题：先恢复原 researcher 补充；仍不足则第二调研代理交叉验证；再不行由 Claude 编排直读关键代码，`--orchestrator=codex` 模式下且第二轮仍无解时可调 Codex A 定向阅读
- plan / acceptance / review 问题：升级 Codex 到 `gpt-5.5`
- Claude developer / tester 问题：升级当前类别 Claude provider 到 DeepSeek V4
- MiniMax 额度不足：直接切 DeepSeek V4

## 3. 聚合返工

同一类别、同一轮、同一 owner 的问题先聚合再返工。

## 4. 先易后难

- 容易解决的先做完。
- 复杂项可标 `SKIPPED_DEFER_NEXT_TIER`。
- 不要让一个复杂问题阻塞整类所有简单问题。

## 5. 相似返工上限

- 同一问题最多自动进行两轮相似修复。
- 第二次仍失败时，必须补证据、换假设、升级模型或更换会话。
- 不得无限试错。
