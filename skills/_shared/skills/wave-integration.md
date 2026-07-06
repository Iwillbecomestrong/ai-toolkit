# Wave Integration

规则：

- 最多并行 3 类，但不能强制凑满。
- 先画依赖图，再决定每个 wave。
- 每个类别必须独立 worktree、branch、责任身份和提交。

启动并行前 → `parallel_safety_check` 钩子。

集成时：

1. 创建 integration worktree
2. 按顺序合并
3. 每合并一类做快速集成检查
4. wave 结束后再做整批集成测试

排查顺序：

- 单类问题读一类文档
- 双类冲突读两类文档
- 真正三方问题才读三类文档
