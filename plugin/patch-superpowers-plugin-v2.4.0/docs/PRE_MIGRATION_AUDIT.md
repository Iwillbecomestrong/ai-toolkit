# v2.3.0 → v2.4.0 审查

## 结论
v2.3.0 是可安装 Overlay，不是 Claude Code 原生插件：缺少 `.claude-plugin/plugin.json`，Skill/Agent 通过复制进入全局或项目目录，名称没有插件命名空间。

## 必须修复
1. 转为原生插件根结构：manifest、skills、agents、bin、config。
2. 所有自定义 Skill/Agent 使用 `patch-` 名称。
3. 不修改原 Superpowers；通过插件命名空间隔离。
4. 头脑风暴输入分类为 MUST_FOLLOW / CONFIRMED_FACTS / UNKNOWN / REFERENCE_ONLY_PATHS。
5. Sol 第一次不读取参考正文；无法独立形成方案时才申请。
6. 参考技术声明必须验证为 CONFIRMED 才能进入计划。
7. 保留两阶段 Sol 规划、Claude Plan Challenger、Luna 审查和 DAG READY 调度。

## Hook 决策
v2.4.0 不包含 hooks。插件仍是合法自包含插件，但门禁依赖 Skill 指令与校验脚本，不是系统级 PreToolUse 阻断。Hook 可在后续版本独立设计。
