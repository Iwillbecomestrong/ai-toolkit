# Patch Superpowers Plugin v2.4.0

中文、多 Agent、两阶段规划与证据门禁的 Claude Code 原生插件。

## 主要角色
- Sol Core/Detailed/Repair Planner：Codex CLI `gpt-5.6-sol + medium`
- Luna Task/Integration Reviewer：Codex CLI `gpt-5.6-luna + medium`
- Claude Agents：Investigator、Plan Challenger、TDD Implementer、Integration Operator

## 使用

临时测试：
```powershell
claude --plugin-dir .
```

持久安装：
```powershell
pwsh -File .\Install.ps1 -CleanLegacyOverlay
```

启动：
```text
/patch-superpowers:patch-using-superpowers
```

## Hook
本版没有 `hooks/`。它仍是原生插件；只是强制门禁由 Skill + Python 校验器实现，而非 PreToolUse 系统阻断。
