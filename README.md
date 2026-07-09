# 集中式 AI Skills / Plugins 仓库

`G:\ai-toolkit\` 是所有 AI 编程 CLI 工具的 skills 和 plugins 的单一来源，通过 Syncthing 在两台 Windows 11 电脑间同步。

> 这个目录以后可能还会扩展到其他 AI 工具配置（hooks、settings、commands 等），不只是 skill/plugin。

## 目录

1. [支持的框架](#支持的框架)
2. [PC#1 (writer) 首次配置](#pc1-writer-首次配置)
3. [PC#2 (新电脑) 首次配置](#pc2-新电脑-首次配置)
4. [日常使用](#日常使用)
5. [关键设计点](#关键设计点)
6. [Lessons L1~L9 (踩坑经验)](#lessons-l1l9-踩坑经验)
7. [Agent 共享记忆 (agent-memory/)](#agent-共享记忆-agent-memory)
8. [记忆整理工作流](#记忆整理工作流)
9. [故障排查](#故障排查)
10. [Skill 使用追踪与定期清理](#skill-使用追踪与定期清理)
11. [升级路径](#升级路径)
12. [项目记忆](#项目记忆)
13. [AGENTS.md 模板](#agentsmd-模板)

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
| Cline (Chinese) | `~/Documents/Cline/Rules/` | — | VS Code 插件；Cline 读 Rules/ 下 .md 作为全局规则；通过 `AGENTS.md` 或 `.clinerules` 也可项目级集成 |
| AionUi | `%APPDATA%/AionUi/config/skills` | — | 桌面应用 |
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
   powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\install-all.ps1
   ```
   日志写到 `G:\ai-toolkit\install.log`。

6. 验证：启动 `claude` 跑 `/skills` 看是否看到集中的 skill。

## PC#2（新电脑）首次配置

1. 同样 `winget install Syncthing.Syncthing`。

2. 打开 `http://localhost:8384`，记下 PC#2 的 Device ID，抄给 PC#1。

3. PC#1 已经 share 后，PC#2 的 GUI 会出现 `central-toolkit` 邀请。点 Accept → Folder Path 填 `G:\ai-toolkit` → Share with PC#1 → Send & Receive。

4. 等待同步完成（GUI 显示 "Up to Date"），几分钟到几十分钟取决于首次同步量。

5. 跑一次 `install-all.ps1` 让各框架落盘：
   ```powershell
   cd G:\ai-toolkit
   powershell -ExecutionPolicy Bypass -File .\install-all.ps1
   ```

6. 启动 `claude`、`codex` 等工具，验证能看到 PC#1 上同样的 skill。

7. PC#2 上**不要 `git commit`**。每台机器各自有独立的 `.git/`（syncthing 不会同步 `.git/`，见 `.stignore`）。

7.5. 初始化嵌套 submodule(两层):
```bash
cd G:\ai-toolkit
powershell -ExecutionPolicy Bypass -File .\init-submodules.ps1
```
此脚本跑两层 `git submodule update --init --recursive`:
- 1 层(主仓): `skills/` + `agent-memory/`
- 2 层(skills 子仓): `autocontents-skill/` + `mdtolatex/` + `md-to-docx/`

## 嵌套 Submodule 结构 (2026-07-09 重构后)

主仓拆为嵌套结构:
- **主仓** = scripts + 4 个项目记忆 + `.gitmodules`
- **2 个 submodule**: `skills/` 整体 + `agent-memory/`
- **3 个 sub-submodule** (在 `skills/` 内): `autocontents-skill` / `mdtolatex` / `md-to-docx` 各自独立 SemVer + CHANGELOG
- **6 个 skill 在 skills/ 子仓直管**: `auto-dev` / `auto-code-android-dev` / `auto-dev-check` / `auto-dev-resume` / `chatgpt-input-output` / `workflow-router`(加 `_shared/`)

**改子子仓后的提交流程**:
```bash
# 一键 commit + tag + push + 上层引用更新
powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\bump-skill.ps1 -Skill autocontents-skill -Type minor -Message "added XX"
```

**改 agent-memory 后的提交流程**:
```bash
cd G:\ai-toolkit\agent-memory
$EDITOR 01_globel.md
git add -A && git commit -m "..." && git push origin main
cd ..
git add agent-memory && git commit -m "bump agent-memory"
```

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

4. 跑 `install-all.ps1`：
   ```powershell
   powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\install-all.ps1
   ```

5. Syncthing 在几十秒内把 `skills/<name>/` 同步到 PC#2。PC#2 上手动跑一次 `install-all.ps1` 让框架落盘。

### 加插件（Claude 或 Copilot）

1. 把 marketplace 目录丢到 `G:\ai-toolkit\plugins\claude\<name>\` 或 `G:\ai-toolkit\plugins\copilot\<name>\`。

2. 提交 + 跑 `install-all.ps1`。

3. 重启对应的 CLI（`claude` / `copilot`）让框架扫描新 marketplace。

## Lessons L1~L9 (踩坑经验)

> 简版在 `agent-memory/01_globel.md` (只有 gurobipy 一条), 详版留底在仓库根 `lessons.md` (git 跟踪), 完整版随 distill 推到 framework 配置。

### L1: install-all.ps1 绝不能用 exclusive 模式

v1 用 "exclusive" 模式, 首次跑就把 codex/mimo/codewhale 的内置 skill 全删了 (5+1+20+ 个)。**用 additive 模型**: 只覆盖 src 里的, 绝不删 dst 里的未知项。验证: 现在跑 `install-all.ps1`, log 里永远不应该看到 `removing stale:`。

### L2: PowerShell `$PSScriptRoot` 通过 `-File` 调用时为空

`powershell -File script.ps1` 调脚本时, `$PSScriptRoot` 是空字符串, 导致 `Resolve-Path` 报错。修复: 加 `$MyInvocation.MyCommand.Path` fallback。v1 install-all.ps1 已包含。

### L3: `git add <file> <file>` + `git commit` 有时会全部提交

用户说不要自动 commit marketplace 导入的 skill, 用 `git add .gitignore README.md && git commit` 想只提交 2 个文件, 结果 commit 了 13,993 个文件。修复: commit 前先 `git status --short | head` 看一眼, 或 `git diff --cached --stat` 确认。

### L4: Syncthing 会自动跟踪带 `.stfolder/` 标记的目录

从 `G:\skill` 改名为 `G:\ai-toolkit` 后, syncthing 自动添加了 folder 配置 (无需手动 add)。但要先确认 marker 文件存在, 否则同步可能出问题。

### L5: Codex CLI 把 skill 解压到 `~/.codex/skills/.system/`, 不是 `~/.codex/skills/`

v1 manifest.json 把 codex 的 dst 写成 `~/.codex/skills/`, 找不到。改成 `~/.codex/skills/.system/` 后才正常。验证: 跑一次 codex CLI, 等它把内置 skill 解压到 `.system/` 就能看到。

### L6: Mimo 的 skill 路径带版本号 `0.1.3`

Mimo 用 tarball 解压, 路径是 `~/.local/share/mimocode/builtin_skills/0.1.3/skills/`。如果 mimo 升级到 0.1.4, 路径会变。修复: manifest.json 里硬编码 `0.1.3`, 升级 mimo 后要同步改。

### L7: Winget 装完 syncthing 要关终端重开才能用 `syncthing` 命令

`where syncthing` 找不到, 但 GUI 能访问 (8384 端口在跑)。修复: 关掉当前 bash/PS, 重开。

### L8: gurobipy 经验

简版在 `01_globel.md` (PC#1 Python 3.14 site-packages, 非 conda, 与 Gurobi Optimizer 主版本一致)。详版 (建模/求解/资源/版本兼容) 在 `lessons.md` L8 节。

### L9: FSTSP-P 复现项目位置

`G:\科研\组会\fstsp_priority_gurobi\`。真要查时 cd 进去, 不用记忆详细内容。

## 关键设计点

### 共享 skills 目录（`~/.agents/skills/`）

**`~/.claude/skills/`、`~/.qoder/skills/`、`~/.copilot/...` 都是符号链接**，实际目标都是 `~/.agents/skills/`。
- 所以 `install-all.ps1` 直接写到 `~/.agents/skills/`，一次写就点亮 Claude + Copilot + Qoder 三个工具。
- 走符号链接链写更脆弱，所以 install-all.ps1 跳过中间层。

### `.stignore` 关键配置

```
(?d).git/
```
**这一行是核心**。没有它 syncthing 会同步两台机器各自的 `.git/` 内部状态（HEAD、refs、objects），互相覆盖直接损坏仓库。

### `install-all.ps1` 幂等性

- 重复跑不会重复复制。
- 全部 framework 用 additive 模型：只覆盖 `skills/` 里有的、绝不删 dst 里的未知项（保护框架内置 skill 和运行时安装的 skill）。
- 想下线某个 skill 时，手动从对应 framework 目录删除，或以后加 stub SKILL.md 机制。

### 框架跳过

- **MoltBot**（v0.1.0）：框架无 skill 系统，install-all.ps1 直接跳过。
- **Gemini**（CLI 0.47.0）：有 `~/.gemini/skills/` 但当前版本无加载器，install-all.ps1 会 stage 文件但不会生效（升级 Gemini 后会自动生效）。

## Agent 共享记忆 (agent-memory/)

每个 Agent（Claude、Codex、Mimo...）各自会产生大量上下文相关的"原始记忆"——偏好、规则、项目背景、踩坑教训。

新结构（v3，2026-07-09，编号反映处理等级）：

```
agent-memory/
├─ 00_inbox/                 # 原始 (任何框架/AI 先丢这里, 带 source 标签)
├─ 01_globel.md              # 全局记忆 (单一文件, 总加载, 极简)
├─ 02_topics/                # 长主题记忆 (按需加载, 暂时空)
├─ 03_agents/<x>.md          # 框架专属 (AI 编辑, 你核查)
└─ 04_distilled/<x>.md       # 公共+框架 合并输出 (gitignored, 自动生成)
```

**编号意义**: `00_` 原始 → `01_` 全局加载 → `02_` 按需主题 → `03_` 框架专属 → `04_` 合并输出。处理等级递增。

### 命令

```powershell
# 看 agent-memory 结构
powershell -ExecutionPolicy Bypass -File .\distill-memory.ps1 -List

# 只生成本地 04_distilled/（默认，不会动 framework）
powershell -ExecutionPolicy Bypass -File .\distill-memory.ps1

# 生成 + 推到 framework 规则位置（覆盖 ~/.claude/CLAUDE.md 等）
powershell -ExecutionPolicy Bypass -File .\distill-memory.ps1 -Apply -Confirm
```

### 同步策略

- `agent-memory/` 整个目录通过 Syncthing 在两台 PC 间同步
- `04_distilled/` 是生成的，git 忽略但 syncthing 仍然同步（任何 PC 跑 distill-memory.ps1 都会让两边一致）

## 记忆整理工作流

> **目标**：inbox 里的原始经验，经过 AI 提纯 + 人工审核，分发到全局记忆 (`01_globel.md`) / 长主题 (`02_topics/<topic>.md`) / 框架专属 (`03_agents/<x>.md`)，再由 distill-memory.ps1 组合推送到 framework 配置。

### 时机

- 默认**每周一次** (例如周一早上)
- 用户明确要求时**立刻跑**

### 步骤

1. **收集**: 检查 `agent-memory/00_inbox/*.md`, 列出待处理的原始经验
2. **AI 提纯**: AI 阅读原始材料，提议:
   - 全局短/稳定 → 写入 `01_globel.md` (极简, 不超过 10 行)
   - 主题长内容 → 写入 `02_topics/<topic>.md` (按需加载)
   - 框架专属 → 写入 `03_agents/<framework>.md`
   - 过期/重复 → 标记删除
3. **人工审核** (同时给用户看):
   - **原始材料** (00_inbox/<topic>.md) 完整内容
   - **提纯后** 拟写入目标文件的 diff
   - 用户确认后 AI 才动文件
4. **分发**: AI 实际写入目标文件, 归档 inbox 内容
5. **重蒸馏**: 跑 `distill-memory.ps1` 重新生成 `04_distilled/<x>.md`
6. **(可选) 推送**: 人工决定是否 `distill-memory.ps1 -Apply -Confirm` 把 distilled 内容推到 framework 实际配置 (`~/.claude/CLAUDE.md` 等)

### 不跑这个工作流时

- 不要主动读 00_inbox/ (按需)
- 不要主动改 `01_globel.md` / `02_topics/` / `03_agents/` (除非用户要求)
- 不要直接编辑 framework 配置 (`~/.claude/CLAUDE.md` 等), 走 distill 流程

## 故障排查

| 症状 | 原因 / 解决 |
|---|---|
| 框架看不到 skill | 重启 CLI；检查 `~/.agents/skills/<name>/SKILL.md` 是否存在 |
| `install-all.ps1` 报 `FATAL: manifest.json not found` | 不在 `G:\ai-toolkit\` 里跑，或者 manifest.json 损坏 |
| Git 说 "dubious ownership" | `git config --global --add safe.directory 'G:/ai-toolkit'` |
| 两台机器同步时 `.git/` 出错 | 确认 `.stignore` 有 `(?d).git/` |
| Syncthing GUI 显示 "Local Additions" 堆积 | 有别的进程在写 `G:\ai-toolkit\`，加进 `.stignore` |
| MoltBot 段在 log 里是 SKIPPED | 正常，框架当前版本无 skill 系统 |
| `distill-memory.ps1` 报告找不到 `agent-memory/` | 不在 `G:\ai-toolkit\` 里跑 |
| distilled/<x>.md 是乱码 | 不应该出现; 用 `xxd <file> \| head` 检查 BOM。distill-memory.ps1 已经强制 UTF-8 NO BOM |

## Skill 使用追踪与定期清理

### 机制

`usage.json` 记录每个 skill 的使用情况：

```json
{
  "last_cleanup": "2026-07-01",
  "skills": {
    "mdtolatex": {
      "installed_date": "2026-07-01",
      "last_used": "2026-07-01",
      "use_count": 3
    }
  }
}
```

### 记录使用

每次使用 skill 后，Claude（或 agent）应更新 `usage.json`：

```powershell
# 手动更新（由 agent 在调用 skill 后执行）
python -c "
import json, datetime
path = r'G:\ai-toolkit\usage.json'
with open(path) as f: data = json.load(f)
name = 'mdtolatex'  # skill 名称
if name not in data['skills']:
    data['skills'][name] = {'installed_date': str(datetime.date.today()), 'last_used': str(datetime.date.today()), 'use_count': 0}
data['skills'][name]['last_used'] = str(datetime.date.today())
data['skills'][name]['use_count'] += 1
with open(path, 'w') as f: json.dump(data, f, indent=2, ensure_ascii=False)
"
```

### 定期清理

每月运行一次清理脚本，删除 30 天未使用的 skill：

```powershell
# 交互式（会询问确认）
powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\cleanup-unused-skills.ps1

# 自动模式（直接删除所有过期 skill，适合 cron）
powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\cleanup-unused-skills.ps1 -Auto

# 自定义天数（如 60 天未用才清理）
powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\cleanup-unused-skills.ps1 -Days 60
```

清理流程：
1. 脚本扫描 `usage.json`，找出超过 30 天未使用的 skill
2. 列出待清理 skill 并询问用户确认（`-Auto` 跳过确认）
3. 从 `G:\ai-toolkit\skills/` 和所有框架目录中删除
4. 更新 `usage.json`

### 定时任务

可以用 Windows 任务计划程序或 Claude 的 `/schedule` 定期提醒：

```powershell
# 每月 1 号提醒清理
schtasks /create /tn "SkillCleanup" /tr "powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\cleanup-unused-skills.ps1" /sc monthly /d 1 /st 09:00
```

## 升级路径

将来 v2 可能加：

- **开机自启动检测新 commit 自动安装**：用户在每次开机时自动看到 PC#1 上的新 skill
- **框架特定覆盖**：当某个 skill 在 Codex 需要不同 frontmatter 时，单独建覆盖目录
- **Git push 到远程**：在 PC#1 加 `git remote add origin`，PC#2 通过 `git pull` 拿历史（独立于 syncthing）
- **插件自动 clone upstream**：从 GitHub 拉最新 marketplace 而不是 stage-only
- **目录扩展**：除了 `skills/` 和 `plugins/`，可以加 `hooks/`、`commands/`、`mcp-configs/` 等子目录，install-all.ps1 按 manifest 分发
- **distill-memory.ps1 支持更多 framework 规则位置**：等 framework 升级支持标准全局规则文件时启用
- **02_topics/ 内容增多后考虑自动去重**：用 embedding 相似度合并重复内容

---

## 项目记忆

> 本仓库的项目记忆集中在 `agent-memory/01_globel.md` (全局, 极简, 总是加载) + `agent-memory/02_topics/` (长主题, 按需) + `agent-memory/03_agents/` (框架专属) + `agent-memory/04_distilled/` (合并输出, 自动)。
>
> **在 ai-toolkit 仓库工作的 Agent**: 加载 `01_globel.md` 就够; 问具体细节时再 Read 对应文件。
>
> **在任何其他项目的 Agent**: 读 `~/.claude/CLAUDE.md` (由 distill-memory.ps1 定期分发), 里面是 ai-toolkit 的完整记忆。

---

## AGENTS.md 模板

> 把下面 `[TEMPLATE BEGIN]` 和 `[TEMPLATE END]` 之间的内容复制到任意项目根目录（保持文件名 `AGENTS.md` 或重命名为 `.clinerules`），即可让 Cline / Claude Code / GitHub Copilot / Qoder 等支持 AGENTS.md / .clinerules 标准的工具识别 G:\ai-toolkit 大本营。

```
[TEMPLATE BEGIN]
# AGENTS.md — Project-level AI Toolkit Reference

> **本文件模板**：把本文件复制到任意项目根目录（保持文件名 `AGENTS.md` 或重命名为 `.clinerules`），即可让 Cline / Claude Code / GitHub Copilot / Qoder 等支持 AGENTS.md / .clinerules 标准的工具识别 G:\ai-toolkit 大本营。

## 关于 G:\ai-toolkit

本项目使用集中式 AI 工具 skill 仓库 `G:\ai-toolkit\`（与本项目文件无关，是单独的 skill 大本营）。

- **位置**：`G:\ai-toolkit\`（Windows 绝对路径）
- **同步**：通过 Syncthing 在两台 PC 间同步；通过 Git 在 PC#1 上做版本管理
- **结构**：
  - `skills/<name>/SKILL.md` — 每个 skill 的源文件（含 YAML frontmatter）
  - `plugins/` — Claude / Copilot 插件
  - `agent-memory/` — 跨工具共享记忆
  - `install-all.ps1` — 把 skill 派发到所有框架

## 使用 skill

当用户要求执行某个特定 skill 描述的任务时：

1. 读取 `G:\ai-toolkit\skills\<skill-name>\SKILL.md` 获取完整执行流程
2. 按 skill 里的 SOP 步骤执行
3. **不要在执行时简化或跳过 skill 中的检查清单**——它们是经过验证的关键节点

## 添加新 skill

如果本项目需要新的 skill（例如 `my-project-task`）：

1. 在 `G:\ai-toolkit\skills\my-project-task\SKILL.md` 创建文件
2. 提交到 Git（PC#1）：`git add skills/my-project-task && git commit -m "feat(my-project-task): initial version"`
3. 跑 `powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\install-all.ps1` 同步到所有框架
4. Syncthing 几十秒内把新 skill 同步到 PC#2

## 沉淀经验

项目中学到的非项目专属经验（例如"如何配置 Gradle 多模块测试"）应写入 `G:\ai-toolkit\agent-memory\inbox\`，并标注主题。定期提纯到 `shared/` 或 `agents/<framework>.md`。

## 不要做的事

- **不要在 `G:\ai-toolkit\skills/` 之外创建 skill**——所有 skill 必须先在大本营注册
- **不要假设 skill 已安装到本项目**——每次使用前先确认框架已加载
- **不要直接编辑 `Documents/Cline/Rules/<skill>/`**——它会被 install-all.ps1 覆盖

## 故障排查

- 工具看不到 skill → 跑 `install-all.ps1` 并重启工具
- 详细诊断 → `cat G:\ai-toolkit\install.log`
- 仓库本身问题 → 读 `G:\ai-toolkit\README.md`
[TEMPLATE END]
```