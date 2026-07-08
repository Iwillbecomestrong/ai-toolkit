# Category Planning

分类后由 DeepSeek V4 Pro planner / OpenCode-OMO hyperplan 做类别计划（`plan_must_be_agent` 钩子）。

计划至少覆盖：

- 目标与非目标
- 允许修改范围
- 文件与调用链
- 风险点
- 快速自检
- 关键中途检查点
- 正式测试
- 验收标准
- 是否需要独立技术审查

开发代理首次进入、计划实质变化或新会话接手时，必须完整阅读：

- `REQUIREMENTS.md`
- `CODE_CONTEXT.md`
- `DECISIONS.md`
- `PLAN.md`
- 当前开放问题
