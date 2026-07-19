# Changelog

## 2.4.0
- 转为 Claude Code 原生插件。
- 所有自定义 Skill/Agent 加 patch 前缀并获得插件命名空间。
- 新增 MUST_FOLLOW / CONFIRMED_FACTS / UNKNOWN / REFERENCE_ONLY_PATHS 分类。
- 仅供参考默认 NOT_READ；独立调查无法形成方案时才定点读取。
- 未验证参考声明不得进入计划。
- 保留 Core Plan → 用户批准 → Detailed Plan 的两阶段 Sol 流程。
- 不包含 Hook。
