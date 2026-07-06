# Multi-Agent Core AI README

## 1. 系统目标

把“多个需求或 Bug 一次性交付”的流程改成：主编排先理解真实目标、调研和澄清，再统一分类；低耦合类别支持受控并行；同类需求统一规划，类内逐项开发，整类统一测试和验收，详细内容走文件交接，主会话只保留轻量状态。

## 2. 角色架构

编排后端由 `--orchestrator=` 参数决定：

### 默认（`--orchestrator=codex`）
- `Codex A`：主编排，默认 `gpt-5.4`
- `Codex B`：计划 + 甲方验收，默认 `gpt-5.4`，必要时升 `gpt-5.5`
- `Codex C`：独立技术审查，默认 `gpt-5.4`，高风险时升 `gpt-5.5`
- `multi-agent-researcher`
- `multi-agent-developer` / `multi-agent-tester`
- `multi-agent-brainstorm` / `multi-agent-writing`

### `--orchestrator=reasonix`
- `Reasonix` 主编排：本会话运行在 Reasonix，编排者固定使用 **deepseekV4pro**
- `Codex` 开发者：deepseekV4pro/flash 可选（任务复杂度决定）
- `Codex` 测试者：固定使用 **deepseekV4flash**
- 不需要 Codex A/B/C——Reasonix 一站式编排，Codex 只做执行
- `multi-agent-researcher`
- `multi-agent-developer` / `multi-agent-tester`
- `multi-agent-brainstorm` / `multi-agent-writing`

## 3. 强制规则

1. 谁开发谁修改。
2. 谁发现问题谁验证到关闭。
3. 第一次返工失败就要检查问题出在哪。
4. 模型规则按 `--orchestrator` 模式执行：
   - Codex 模式：Claude provider 从 MiniMax 开始，失败时切 DeepSeek V4
   - Reasonix 模式：编排者 deepseekV4pro（固定），开发者 pro/flash 可选，测试者 flash（固定）
5. 默认先解决能解决的问题，复杂问题可先跳过，最后集中升级处理。
6. 最大并行类别数为 3，但不能为了凑满并行度强行分组。
7. 开发和测试首次进入类别时，必须完整阅读需求、上下文、决策、计划和当前开放问题。
8. 责任身份固定，但聊天会话可以恢复、替换或升级。

## 4. 安装与文件

核心 skill 文件：

- `SKILL.md`
- `WORKFLOW.md`
- `ROUTING.md`
- `REPORT_FORMATS.md`
- `AI_README.md`
- `WORKTREE_GUIDE.md`

模板文件：

- `templates/STATE.json`
- `templates/ISSUES.json`
- `templates/ORCHESTRATOR_STATE.json`
- `templates/AGENT_REGISTRY.json`
- `templates/ISSUE_REGISTRY.json`
- `templates/INTEGRATION_STATE.json`
- `templates/manifest.json`
- `templates/AGENT_RETURN_TEMPLATE.md`
- `templates/NEXT_AGENT_PROMPT_TEMPLATE.md`
- `templates/ISSUE_TEMPLATE.md`

脚本文件：

- `scripts/multi-agent-core/check-environment.ps1`
- `scripts/multi-agent-core/new-category-worktree.ps1`
- `scripts/multi-agent-core/new-integration-worktree.ps1`
- `scripts/multi-agent-core/run-codex-plan.ps1`
- `scripts/multi-agent-core/run-codex-review.ps1`

## 5. 并行与 Worktree

并行是按类别并行，不是多开发代理同时改同一工作目录。

要求：

- 最多 3 个类别并行
- 每个类别独立 worktree
- 每个类别独立 branch
- 每个类别独立 developer / tester
- 每个 wave 单独集成
- 集成失败按单类 / 双类 / 三类最小读取顺序排查

主状态优先使用：

- `.collab-work/STATE.json`
- `.collab-work/ISSUES.json`
- `.collab-work/runs/<task-id>/<category-id>/manifest.json`

兼容性文件只在脚本仍依赖时同步。

## 6. 适用范围

这是通用协作核心，不绑定 Android、Web、Python 或某个具体项目。

项目特定能力应作为 profile 叠加，例如：

- `multi-agent-android`
- `multi-agent-web`
- `multi-agent-python`
- `multi-agent-docs`

## 7. Claude 自动压缩配置（仅 Codex 模式需要）

用户级配置文件：`%USERPROFILE%\.claude\settings.json`

目标：

- 保留现有全部配置
- `env.CLAUDE_AUTOCOMPACT_PCT_OVERRIDE = "70"`
- 不固定上下文窗口

## 8. 完成标准

- skill 文档已更新
- 支持调研、类别批处理、代理复用、文件交接、主编排轻量恢复
- 支持最大并行 3 和 worktree 隔离
- 支持第一次返工失败后的主编排诊断
- 支持两种编排模式：`codex`（默认）、`reasonix`
- Reasonix 模式：编排者 deepseekV4pro 固定，开发者 pro/flash 可选，测试者 flash 固定
- Codex 模式：Codex A 编排 + Codex B/C 固定职责和模型升级
