# Skill 修改说明

CHANGE_NAME: auto-dev-change-20260706-iron-law
SOURCE_SESSION: reasonix-ironwill
SOURCE_TASK: AI 绕过 auto-dev 流程直接改代码
BASE_SKILL_VERSION: post-merge (e445025)
BASE_COMMIT: e445025

## 为什么要改

AI 即使有 PreToolUse hook，还是会在思考中绕过流程——说"这是小问题不需要走完整编排"然后直接读代码。
需要 prompt 层铁律明确禁止这种行为。

## 改了什么

- auto-dev SKILL.md 开头新增 ⛔ 铁律 4 条
- auto-code-android-dev SKILL.md 开头新增相同铁律

## 风险

RISK: LOW — 纯提示词修改

## 是否建议合并

MERGE_RECOMMENDATION: YES
