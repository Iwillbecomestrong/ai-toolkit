# 迁移指南

1. 备份 v2.3.0 standalone overlay。
2. 运行 `Install.ps1 -CleanLegacyOverlay`，安装到 `~/.claude/skills/patch-superpowers/`。
3. 原版 Superpowers 的 `brainstorming`、`writing-plans`、`using-superpowers` 不修改、不删除。
4. 重启 Claude Code 或运行 `/reload-plugins`。
5. 使用 `/patch-superpowers:patch-using-superpowers` 启动。
6. 本地开发可运行 `claude --plugin-dir <插件目录>`；ZIP 可直接作为 `--plugin-dir` 输入（需要支持该功能的 Claude Code 版本）。
