# Skill 修改说明

CHANGE_NAME: auto-dev-change-20260706-shared-core-hooks
SOURCE_SESSION: reasonix-ironwill
SOURCE_TASK: auto-dev & multi-agent-core 综合改造
BASE_SKILL_VERSION: current (pre-shared-core)
BASE_COMMIT: ef596f3

## 为什么要改

1. auto-dev 和 multi-agent-core 有大量重复内容（WORKFLOW、ROUTING、子 skill、模板），改一处另一处不同步
2. 两个 skill 只有 prompt 层面的规则，没有系统级强制门禁——模型经常跳过关键流程（如直接写 plan.md、无验证就提交）
3. 没有 Git worktree 版本管理，skill 修改不可追踪、不可回滚

## 改了什么

- 抽取 `_shared/` 共享核心目录，auto-dev 和 multi-agent-core 改为引用共享文件
- 新增 `HOOKS.md`，定义 7 个强制门禁钩子
- 新增 `scripts/auto_dev_guard.py`，实现 PreToolUse 级别的系统门禁
- 新增 `SKILL_VERSIONING.md`，定义 Git worktree 版本管理规范
- 精简 auto-dev 和 multi-agent-core 的 SKILL.md，去掉"Codex 友好"等偏袒描述
- 更新 `install-all.ps1` 使 `_shared/` 同步到各 framework

## 新增了什么功能

- `plan_must_be_codex` 钩子：主编排者禁止直接写 plan.md
- `codex_output_visible` 钩子：Codex 子代理输出前台展示
- PreToolUse 4 大门禁：未批准计划禁改源码、编排者禁写计划、无验证禁提交、禁搬运长文档
- Stop Hook 轻量提醒
- UserPromptSubmit Hook 自动初始化 STATE.json
- auto_dev_guard.py：可被 Claude Code hooks 系统调用的 Python guard 脚本

## 影响范围

- 影响 auto-dev 和 multi-agent-core 的全部阶段
- 影响所有子代理的 PreToolUse 行为
- 影响 install-all.ps1 同步逻辑
- 不影响现有任务的 STATE.json 结构（向后兼容）

## 风险

RISK: MEDIUM

- auto_dev_guard.py 需要 Claude Code hooks 系统支持，如果 hooks 未配置则不生效
- _shared/ 引用是语义化的，依赖各自 SKILL.md 中的引用说明

## 是否建议合并

MERGE_RECOMMENDATION: YES

## 合并前需要验证

- [ ] install-all.ps1 正确同步 _shared/ 到各 framework
- [ ] auto-dev SKILL.md 引用 _shared 的路径正确
- [ ] multi-agent-core SKILL.md 引用 _shared 的路径正确
- [ ] auto_dev_guard.py 可通过 `python auto_dev_guard.py pretooluse .ai-work < test_input.json` 测试
- [ ] 所有 gate 的 allow/deny 逻辑正确
