# Patch Superpowers Plugin v2.4.0 设计

这是一个 Claude Code 原生插件，提供中文 Skill、Claude 子代理、Codex Sol/Luna 路由器、规划与审查模板、DAG 工具和安装脚本。

核心变化：原版 Superpowers 完全保留；Patch 资产全部命名隔离；输入先分类；必须遵守文件先读；仅供参考只记录路径并延迟读取；参考声明验证后才能成为计划依据；Sol 先给用户看 Core Plan，再展开详细 Plan。

本版不包含 Hook，因此不会自动拦截所有违规工具调用。执行前必须运行规划/审查校验器。
