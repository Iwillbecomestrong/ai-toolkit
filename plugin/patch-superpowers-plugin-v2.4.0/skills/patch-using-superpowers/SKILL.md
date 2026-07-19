---
name: patch-using-superpowers
description: Use when a software design, bug fix, refactor, implementation, planning, or multi-agent task should use the Patch Superpowers workflow instead of mixing standalone Superpowers skills.
---

# Patch Superpowers 入口

本插件启用后，软件设计、修 Bug、重构、计划和多 Agent 开发优先使用本插件的 Skill。后续只在 `patch-superpowers:*` 命名空间内路由，不与原版 Superpowers 的同类流程混用。

## 路由

- 需求与设计：`patch-superpowers:patch-brainstorming`
- 两阶段计划：`patch-superpowers:patch-writing-plans`
- 计划对抗审查：`patch-superpowers:patch-challenging-plans`
- DAG 总编排：`patch-superpowers:patch-parallel-dag-development`
- 实施：`patch-superpowers:patch-subagent-driven-development`
- 最终审计：`patch-superpowers:patch-sol-final-audit`

原版 Superpowers 不被修改。只有用户明确要求原版时，才退出 Patch 路由。
