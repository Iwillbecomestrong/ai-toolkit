# Skill 修改说明

CHANGE_NAME: auto-dev-change-20260706-merge-multi-agent-core
SOURCE_SESSION: reasonix-ironwill
SOURCE_TASK: 合并 auto-dev + multi-agent-core + auto-code-android-dev
BASE_SKILL_VERSION: post-shared-core (a80b0e1)
BASE_COMMIT: a80b0e1

## 为什么要改

1. auto-dev 和 multi-agent-core 结构完全相同，只差编排后端参数——没必要分两个 skill
2. auto-code-android-dev 只是引用壳，90% 内容是"见 auto-dev"，独有内容（adb/emulator）可直接并入 auto-dev

## 改了什么

- auto-dev SKILL.md 合并三种编排后端（claude/codex/reasonix）通过 `--orchestrator=` 切换
- 并入 auto-code-android-dev 的 Android 专用内容（`--project=android`）
- 删除 `skills/multi-agent-core/` 目录
- 删除 `IronWill/.claude/skills/auto-code-android-dev/`
- 更新 SKILL_CORE.md 和 HOOKS.md 移除 multi-agent-core 引用

## 影响范围

- 所有引用 multi-agent-core 的地方改为 auto-dev
- install-all.ps1 不再安装 multi-agent-core
- Android 项目直接用 `auto-dev --project=android`

## 风险

RISK: LOW — multi-agent-core 和 auto-dev 内容 99% 相同，合并无功能损失

## 是否建议合并

MERGE_RECOMMENDATION: YES
