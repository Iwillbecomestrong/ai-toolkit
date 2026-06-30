# 集中式 AI Skills / Plugins 仓库

`G:\ai-toolkit\` 是所有 AI 编程 CLI 工具的 skills 和 plugins 的单一来源，通过 Syncthing 在两台 Windows 11 电脑间同步。

> 这个目录以后可能还会扩展到其他 AI 工具配置（hooks、settings、commands 等），不只是 skill/plugin。

## 支持的框架

| 框架 | Skills 路径 | Plugins 路径 | 备注 |
|---|---|---|---|
| Claude Code | `~/.agents/skills/` | `~/.claude/plugins/marketplaces/` | 与 Copilot/Qoder 共享 `~/.agents/skills/` |
| OpenAI Codex | `~/.codex/skills/.system/` | `~/.codex/plugins/` | |
| Mimo AI | `~/.local/share/mimocode/builtin_skills/0.1.3/skills/` | — | tarball 解压目录 |
| GitHub Copilot | `~/.agents/skills/` | `%LOCALAPPDATA%/copilot/marketplaces/` | 共享 .agents/skills |
| Qoder | `~/.agents/skills/` | — | 共享 .agents/skills |
| Google Gemini | `~/.gemini/skills/` | — | v1 stage-only（CLI 0.47 无加载器） |
| CodeWhale | `~/.codewhale/skills/` | — | |
| MoltBot | — | — | v0.1.0 无 skill 系统 |

## PC#1（writer）首次配置

1. 安装 Syncthing（用 winget，per-user 自动启动，无需 NSSM）：
   ```powershell
   winget install Syncthing.Syncthing --accept-package-agreements --accept-source-agreements
   ```
   装完关掉终端重开，刷新 PATH。

2. 在 `G:\ai-toolkit\` 里执行下面的初始化（已在本仓库手动完成）：
   ```powershell
   cd G:\ai-toolkit
   git init -b main
   git add -A
   git commit -m "chore: bootstrap central skills repo"
   ```

3. 浏览器打开 `http://localhost:8384`，记下右上角 Actions → Show ID 的 56 位 Device ID。

4. 在 GUI 里 Add Folder：
   - Folder Path: `G:\ai-toolkit`
   - Folder Label: `central-toolkit`
   - Folder Type: Send & Receive
   - Share with: PC#2 的 Device ID

5. 把现有 skills 装到所有框架：
   ```powershell
   powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\install.ps1
   ```
   日志写到 `G:\ai-toolkit\install.log`。

6. 验证：启动 `claude` 跑 `/skills` 看是否看到集中的 skill。

## PC#2（新电脑）首次配置

1. 同样 `winget install Syncthing.Syncthing`。

2. 打开 `http://localhost:8384`，记下 PC#2 的 Device ID，抄给 PC#1。

3. PC#1 已经 share 后，PC#2 的 GUI 会出现 `central-toolkit` 邀请。点 Accept → Folder Path 填 `G:\ai-toolkit` → Share with PC#1 → Send & Receive。

4. 等待同步完成（GUI 显示 "Up to Date"），几分钟到几十分钟取决于首次同步量。

5. 跑一次 `install.ps1` 让各框架落盘：
   ```powershell
   cd G:\ai-toolkit
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```

6. 启动 `claude`、`codex` 等工具，验证能看到 PC#1 上同样的 skill。

7. PC#2 上**不要 `git commit`**。每台机器各自有独立的 `.git/`（syncthing 不会同步 `.git/`，见 `.stignore`）。

## 日常使用

### 加新 skill

1. 创建 `G:\ai-toolkit\skills\<name>\SKILL.md`（YAML frontmatter 必需，至少包含 `name` 和 `description`）：
   ```markdown
   ---
   name: my-skill
   description: 简短描述，让框架知道何时调用
   ---

   # My Skill

   具体内容...
   ```

2. 可选：加 `scripts/`、`references/`、`assets/` 子目录。

3. 在 PC#1 提交：
   ```bash
   git add skills/<name>
   git commit -m "feat(<name>): initial version"
   ```

4. 跑 `install.ps1`：
   ```powershell
   powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\install.ps1
   ```

5. Syncthing 在几十秒内把 `skills/<name>/` 同步到 PC#2。PC#2 上手动跑一次 `install.ps1` 让框架落盘。

### 加插件（Claude 或 Copilot）

1. 把 marketplace 目录丢到 `G:\ai-toolkit\plugins\claude\<name>\` 或 `G:\ai-toolkit\plugins\copilot\<name>\`。

2. 提交 + 跑 `install.ps1`。

3. 重启对应的 CLI（`claude` / `copilot`）让框架扫描新 marketplace。

## 关键设计点

### 共享 skills 目录（`~/.agents/skills/`）

**`~/.claude/skills/`、`~/.qoder/skills/`、`~/.copilot/...` 都是符号链接**，实际目标都是 `~/.agents/skills/`。
- 所以 `install.ps1` 直接写到 `~/.agents/skills/`，一次写就点亮 Claude + Copilot + Qoder 三个工具。
- 走符号链接链写更脆弱，所以 install.ps1 跳过中间层。

### `.stignore` 关键配置

```
(?d).git/
```
**这一行是核心**。没有它 syncthing 会同步两台机器各自的 `.git/` 内部状态（HEAD、refs、objects），互相覆盖直接损坏仓库。

### `install.ps1` 幂等性

- 重复跑不会重复复制。
- 全部 framework 用 additive 模型：只覆盖 `skills/` 里有的、绝不删 dst 里的未知项（保护框架内置 skill 和运行时安装的 skill）。
- 想下线某个 skill 时，手动从对应 framework 目录删除，或以后加 stub SKILL.md 机制。

### 框架跳过

- **MoltBot**（v0.1.0）：框架无 skill 系统，install.ps1 直接跳过。
- **Gemini**（CLI 0.47.0）：有 `~/.gemini/skills/` 但当前版本无加载器，install.ps1 会 stage 文件但不会生效（升级 Gemini 后会自动生效）。

## 故障排查

| 症状 | 原因 / 解决 |
|---|---|
| 框架看不到 skill | 重启 CLI；检查 `~/.agents/skills/<name>/SKILL.md` 是否存在 |
| `install.ps1` 报 `FATAL: manifest.json not found` | 不在 `G:\ai-toolkit\` 里跑，或者 manifest.json 损坏 |
| Git 说 "dubious ownership" | `git config --global --add safe.directory 'G:/ai-toolkit'` |
| 两台机器同步时 `.git/` 出错 | 确认 `.stignore` 有 `(?d).git/` |
| Syncthing GUI 显示 "Local Additions" 堆积 | 有别的进程在写 `G:\ai-toolkit\`，加进 `.stignore` |
| MoltBot 段在 log 里是 SKIPPED | 正常，框架当前版本无 skill 系统 |

## 升级路径

将来 v2 可能加：

- **开机自启动检测新 commit 自动安装**：用户在每次开机时自动看到 PC#1 上的新 skill
- **框架特定覆盖**：当某个 skill 在 Codex 需要不同 frontmatter 时，单独建覆盖目录
- **Git push 到远程**：在 PC#1 加 `git remote add origin`，PC#2 通过 `git pull` 拿历史（独立于 syncthing）
- **插件自动 clone upstream**：从 GitHub 拉最新 marketplace 而不是 stage-only
- **目录扩展**：除了 `skills/` 和 `plugins/`，可以加 `hooks/`、`commands/`、`mcp-configs/` 等子目录，install.ps1 按 manifest 分发
