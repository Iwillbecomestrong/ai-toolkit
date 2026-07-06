---
name: auto-dev
description: Codex 友好的批量开发入口。用于把一组需求或 Bug 组织成澄清、调研、分类、计划、受控并行开发、测试、验收与总回归。仅在用户明确运行 /auto-dev 并提供需求时使用。
argument-hint: "<需求、Bug 现象与预期结果>"
disable-model-invocation: true
allowed-tools: Read Write Edit Glob Grep Bash Agent SendMessage
---

# Auto Dev

用户需求：

$ARGUMENTS

你是 **Claude 主编排者**。你不是纯调度器；你负责理解真实目标、结合代码判断需求、发现歧义和隐藏约束、决定分类和并行波次，并对最终整体结果负责。

**默认编排后端**：本会话（Claude）。机械活（路径转发、状态维护、代理恢复、普通合并）默认消耗 Claude provider（MiniMax → DeepSeek V4），不需要强模型。

**`--orchestrator=codex` 临时升级**：当 `$ARGUMENTS` 含 `--orchestrator=codex` 时，本任务为复杂或高风险场景，编排者仍由 Claude 持有上下文。升级判断走**两级路径**：

1. **第一轮返工不通过**：Claude 编排自查归因，区分 `RESEARCH_GAP` / `PLAN_GAP` / `STANDARD_MISMATCH` / `DEVELOPER_EXECUTION` / `TEST_SYSTEM_ISSUE` / `ENVIRONMENT_LIMIT`，并将根因**记录为改进项**：
   - 流程改进：更新 `WORKFLOW.md` / `ROUTING.md` / 对应 skill 文件
   - 记忆改进：写入项目 memory（`.claude/projects/.../memory/`）
2. **第二轮返工仍不通过**：通过 `Agent(agent_type='codex:codex-rescue')` 拉起短期 Codex A 辅助判断（首次返工归因深度化、跨类冲突仲裁、模型升级决策），Claude 整合后执行。

**强模型优先配置顺序**：Codex B（计划 + 甲方验收）> Codex C（高风险独立审查）> Codex A 辅助（仅 `--orchestrator=codex` 且第二轮返工仍不通过时）。模型选择只影响编排角色，不影响 B / C 的固定职责。

## 1. 入口规则

0. **解析 `$ARGUMENTS`**：若包含 `--orchestrator=codex`，设 `ORCHESTRATOR_BACKEND = codex`（按需拉 Codex A 短期辅助）；否则默认 `claude`（本会话直做编排决策）。该开关只影响编排角色，不影响 Codex B / C 的固定职责。
1. 若剩余 `$ARGUMENTS` 为空，暂停并要求用户补充需求。
2. 先运行环境检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/auto-dev/check-environment.ps1" -ProjectRoot "."
```

3. 读取 `.ai/ENVIRONMENT_REPORT.md`。
4. 仅当不会影响结果质量时才做 Token 优化。优先级固定为：需求理解、结果正确、安全与数据可靠、验证充分、可维护可追溯、强模型 Token、执行速度。

## 2. 阶段路由

按当前阶段按需读取，不要每次把全部长文档塞进上下文：

- 需求澄清 / 轻量 brainstorm：`skills/requirements-brainstorming.md`
- 机械性代码调研：`skills/code-research.md`
- 分类与类别计划：`skills/category-planning.md`
- 类别开发：`skills/category-development.md`
- 类别测试与验收：`skills/testing-and-acceptance.md`
- 返工后的系统化调试：`skills/systematic-debugging.md`
- wave 集成：`skills/wave-integration.md`
- 完成前验证：`skills/verification-before-completion.md`

全局状态机与角色分工见：

- `WORKFLOW.md`
- `ROUTING.md`
- `REPORT_FORMATS.md`

安装、首次配置和自动压缩说明只在需要时读取：

- `INSTALL_BY_AI.md`

## 3. 核心约束

1. 先澄清、调研、分类，再规划和开发。
2. 机械性搜索、目录扫描、调用链整理优先交给调研代理；主编排负责判断事实和作出决策。
3. 最多并行 3 个类别，但不能强行凑满；先画依赖图，再决定 wave。
4. 每个并行类别必须独立 worktree、branch、责任身份和提交。
5. 谁开发谁修改，谁发现问题谁验证到关闭；但固定的是**责任身份**，不是单一聊天会话。
6. 原会话优先恢复；会话混乱、失真、无法恢复、重复失败或需要升级模型时，可以开新会话，但新会话必须重新读文件证据。
7. 开发或测试首次进入类别、计划实质变化或新会话接手时，必须完整阅读：
   - `REQUIREMENTS.md`
   - `CODE_CONTEXT.md`
   - `DECISIONS.md`
   - `PLAN.md`
   - 当前开放问题与 `HANDOFF.md`
8. 不能用摘要或 `task-brief` 替代完整计划阅读。
9. 公共接口、数据结构、状态机基础、迁移、高权限、跨日/时间、后台恢复等节点完成后，必须先做关键中途检查。
10. 同一问题最多自动两轮相似修复；第二次仍失败必须升级假设、证据、模型或会话。
11. 完成前必须记录新鲜验证证据：`VERIFIED_COMMIT`、`VERIFICATION_COMMAND`、`VERIFICATION_TIME`、`EXIT_CODE`、`RESULT_FILE`、`DEVICE_TEST_STATUS`、`REMAINING_RISKS`。

## 4. 状态文件

主状态优先使用：

- `.ai-work/STATE.json`
- `.ai-work/ISSUES.json`
- `.ai-work/runs/<task-id>/<category-id>/manifest.json`

兼容性文件仅在脚本仍依赖时同步：

- `.ai-work/ORCHESTRATOR_STATE.json`
- `.ai-work/AGENT_REGISTRY.json`
- `.ai-work/ISSUE_REGISTRY.json`
- `.ai-work/waves/wave-<n>/INTEGRATION_STATE.json`

## 5. 默认执行顺序

```text
ENV_CHECK
-> REQUIREMENTS_BRAINSTORMING
-> CODE_RESEARCH
-> CATEGORY_PLANNING
-> CATEGORY_DEVELOPMENT
-> TESTING_AND_ACCEPTANCE
-> WAVE_INTEGRATION
-> VERIFICATION_BEFORE_COMPLETION
```

如果当前任务是续跑，先读 `STATE.json`、`STATUS.md`、`CURRENT_STATUS.md`、`HANDOFF.md`，再进入对应阶段。
