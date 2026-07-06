# Multi-Agent Core Install By AI

这个文件只在安装、首次配置或环境校验时读取，不应在每次开发任务中默认加载。

## 1. 目标

- 校验 `multi-agent-core` 所需模板、代理说明和脚本文件存在
- Codex 模式：开启 `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE = "70"`
- Reasonix 模式：不需要 Claude 配置

## 2. Claude 配置（仅 Codex 模式需要）

用户级配置路径：

- `%USERPROFILE%\.claude\settings.json`

处理规则：

1. 修改前创建时间戳备份。
2. 保留原有 `permissions`、`hooks`、`plugins`、`model`、`mcp`、`statusLine` 与其他 `env`。
3. 加入或更新：
   - `"CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "70"`
4. 没有明确特殊用途时，不要保留固定的 `CLAUDE_CODE_AUTO_COMPACT_WINDOW`。
5. 修改后验证 JSON 合法。

## 3. 必备文件

- `SKILL.md`
- `WORKFLOW.md`
- `ROUTING.md`
- `REPORT_FORMATS.md`
- `AI_README.md`
- `templates/STATE.json`
- `templates/ISSUES.json`
- `templates/manifest.json`
- `templates/AGENT_RETURN_TEMPLATE.md`
- `templates/NEXT_AGENT_PROMPT_TEMPLATE.md`
- `skills/*.md`
- `.claude/agents/multi-agent-*.md`（仅 Codex 模式需要）
- `scripts/multi-agent-core/*.ps1`

## 4. 验证

执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\multi-agent-core\check-environment.ps1 -ProjectRoot .
```

读取：

- `.collab/ENVIRONMENT_REPORT.md`
