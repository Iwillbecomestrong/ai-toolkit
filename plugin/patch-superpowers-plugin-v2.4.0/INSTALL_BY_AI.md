# 给本地 AI 的安装 Prompt

请审查当前目录是合法 Claude Code 插件：`.claude-plugin/plugin.json`、`skills/`、`agents/`、`bin/` 和 `config/` 均位于插件根目录。不要修改原 Superpowers Plugin。

执行：
1. 读取 `docs/PRE_MIGRATION_AUDIT.md` 与 `docs/MIGRATION_GUIDE_ZH.md`。
2. 若 `claude` 可用，先运行 `claude plugin validate . --strict`；失败则停止并报告。
3. 运行 `python Verify-Package.py --source .`。
4. 备份 `~/.claude/skills/patch-superpowers`（若存在）。
5. 运行 `pwsh -File ./Install.ps1 -CleanLegacyOverlay`；没有 PowerShell 时，将当前插件目录完整复制到 `~/.claude/skills/patch-superpowers`。
6. 不得删除或覆盖原版 `brainstorming`、`writing-plans`、`using-superpowers` 等 Superpowers Skill。
7. 重启 Claude Code或运行 `/reload-plugins`。
8. 检查 `/help` 中存在 `/patch-superpowers:patch-using-superpowers`，并检查自定义 Agents 中存在 `patch-superpowers:patch-plan-challenger`。
9. 运行一个小型设计任务，确认流程先生成 INPUT_CLASSIFICATION，再独立调查，参考路径保持 NOT_READ。
10. 报告所有未执行的验证，不得用静态检查冒充真实 Claude 会话验证。
