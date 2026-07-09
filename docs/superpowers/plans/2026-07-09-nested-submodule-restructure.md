# Nested Submodule Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `G:\ai-toolkit\` 从单一 git 仓重构为**嵌套 submodule 结构**,3 个高复杂度 skill(autocontents-skill / mdtolatex / md-to-docx)各自独立 SemVer,skills/ 与 agent-memory/ 拆为独立子仓,主仓仅管 scripts + 4 个项目记忆。

**Architecture:** 主仓 + 2 个 submodule(skills/、agent-memory/) + 3 个 sub-submodule(在 skills/ 内)。所有子仓/子子仓无远端,本地 bare repo 中转(`.git-remotes/`)以便 `git push` 留痕。PC#1 commit 各仓,Syncthing 同步文件;PC#2 跑 `init-submodules.ps1` 一键 init 两层,仍不 commit 任何子仓。

**Tech Stack:** Git 2.x(含 submodule),PowerShell 5.1+,Syncthing(已有),Windows 11。

---

## Global Constraints

- 仓库根:`G:\ai-toolkit\`
- 主仓分支:`main`
- 3 个子子仓统一用 SemVer(`v0.1.0` 起步),CHANGELOG.md 跟踪 breaking/minor/patch
- 所有子仓/子子仓**无远端**,纯本地 bare repo 中转:`G:\ai-toolkit\.git-remotes\`
- `.stignore` 必须加 `(?d).git-remotes/` 和 `(?d).git/`(保护两台 PC .git 不互覆盖)
- PC#2 仍**不 commit 任何子仓**(沿用现有规则)
- 文件名/目录名/commit message 用英文,文档说明用中文
- 每个任务结束 commit,禁止累积
- 任务 1-6 在 PC#1 执行;任务 7-10 涉及文档;任务 11 是 PC#2 验证

---

## File Structure

### 新增文件
| 路径 | 用途 |
|---|---|
| `G:\ai-toolkit\.git-remotes\skills.git\` | skills/ 子仓的 bare 中转 |
| `G:\ai-toolkit\.git-remotes\agent-memory.git\` | agent-memory/ 子仓的 bare 中转 |
| `G:\ai-toolkit\.git-remotes\skills_submodules\autocontents-skill.git\` | 子子仓 bare |
| `G:\ai-toolkit\.git-remotes\skills_submodules\mdtolatex.git\` | 子子仓 bare |
| `G:\ai-toolkit\.git-remotes\skills_submodules\md-to-docx.git\` | 子子仓 bare |
| `G:\ai-toolkit\skills\autocontents-skill\CHANGELOG.md` | 子子仓初始 changelog |
| `G:\ai-toolkit\skills\mdtolatex\CHANGELOG.md` | 子子仓初始 changelog |
| `G:\ai-toolkit\skills\md-to-docx\CHANGELOG.md` | 子子仓初始 changelog |
| `G:\ai-toolkit\skills\.gitmodules` | 子仓声明 3 个 sub-submodule |
| `G:\ai-toolkit\.gitmodules` | 主仓声明 2 个 submodule |
| `G:\ai-toolkit\bump-skill.ps1` | 子子仓 SemVer 提交助手 |
| `G:\ai-toolkit\init-submodules.ps1` | PC#2 一键 init 两层 submodule |

### 修改文件
| 路径 | 修改内容 |
|---|---|
| `G:\ai-toolkit\.gitignore` | 加 `.git-remotes/` |
| `G:\ai-toolkit\.stignore` | 加 `(?d).git-remotes/` |
| `G:\ai-toolkit\README.md` | 加 submodule init/update 步骤 + 提交流程 |
| `G:\ai-toolkit\projects.md` | 更新仓库结构段,Phase 2 加迁移项 |
| `G:\ai-toolkit\skills\autocontents-skill\.git\` | 新建 git 仓(从主仓剥离) |
| `G:\ai-toolkit\skills\mdtolatex\.git\` | 新建 git 仓(从主仓剥离) |
| `G:\ai-toolkit\skills\md-to-docx\.git\` | 新建 git 仓(从主仓剥离) |
| `G:\ai-toolkit\skills\.git\` | 新建 git 仓(从主仓剥离,7 个直管 skill) |
| `G:\ai-toolkit\agent-memory\.git\` | 新建 git 仓(从主仓剥离) |
| `G:\ai-toolkit\skills`(主仓视角) | 变 gitlink 引用子仓 |
| `G:\ai-toolkit\agent-memory`(主仓视角) | 变 gitlink 引用子仓 |

### 暂不修改
- `install-all.ps1`(兼容,无需改)
- `manifest.json`(兼容,无需改)
- `distill-memory.ps1`(已读 `04_distilled/`,无需改)

---

## Task 1: 准备裸仓中转目录 + 更新 ignore

**Files:**
- Create: `G:\ai-toolkit\.git-remotes\skills_submodules\`(空目录)
- Modify: `G:\ai-toolkit\.gitignore`(末尾追加)
- Modify: `G:\ai-toolkit\.stignore`(末尾追加)

**Interfaces:**
- Consumes: 无
- Produces: `.git-remotes/` 目录存在,`git status` 仍干净

- [ ] **Step 1: 创建裸仓中转目录**

```bash
mkdir -p "G:/ai-toolkit/.git-remotes/skills_submodules"
ls -la "G:/ai-toolkit/.git-remotes"
```
预期:看到 `.` `..` `skills_submodules` 三个条目。

- [ ] **Step 2: 更新 .gitignore**

编辑 `G:\ai-toolkit\.gitignore`,在文件**末尾**追加:
```
# Submodule bare repo stash (PC#1 only, syncthing excluded)
.git-remotes/
```

- [ ] **Step 3: 更新 .stignore**

编辑 `G:\ai-toolkit\.stignore`,在文件**末尾**追加:
```
# Submodule bare repos must NOT sync (would corrupt)
(?d).git-remotes/
```

- [ ] **Step 4: 验证 ignore 生效**

```bash
cd G:/ai-toolkit
git check-ignore -v .git-remotes/skills_submodules
```
预期:`.gitignore:42:.git-remotes/	.git-remotes/skills_submodules`(第 42 行可能不同,关键是路径匹配)。

- [ ] **Step 5: 验证 git status 干净**

```bash
cd G:/ai-toolkit
git status --short
```
预期:**只看到本次修改的 `.gitignore` 和 `.stignore`**(如果主仓之前有其他未跟踪改动,本次任务接受的"基线"是那些改动都还在;关键是新增 `.git-remotes/` 目录**不**出现在 untracked 列表里)。

- [ ] **Step 6: Commit**

```bash
cd G:/ai-toolkit
git add .gitignore .stignore
git commit -m "chore: add .git-remotes/ for submodule bare repos

为嵌套 submodule 重构准备本地 bare repo 中转。.stignore 加 (?d).git-remotes/
防止 Syncthing 双向同步损坏 git 仓。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: 抽取 autocontents-skill 为子子仓

**Files:**
- Create: `G:\ai-toolkit\.git-remotes\skills_submodules\autocontents-skill.git\`(bare)
- Create: `G:\ai-toolkit\skills\autocontents-skill\.git\`(从主仓剥离)
- Create: `G:\ai-toolkit\skills\autocontents-skill\CHANGELOG.md`
- Modify: 主仓视角下 `skills/autocontents-skill/` 变 gitlink

**Interfaces:**
- Consumes: `G:\ai-toolkit\skills\autocontents-skill\`(原主仓直管)
- Produces: `autocontents-skill` 是独立 git 仓,有 v0.1.0 tag

- [ ] **Step 1: 创建子子仓的 bare 中转**

```bash
cd "G:/ai-toolkit/.git-remotes/skills_submodules"
git init --bare autocontents-skill.git
ls autocontents-skill.git/
```
预期:看到 `HEAD` `config` `objects` `refs` 等 bare 仓文件。

- [ ] **Step 2: 在主仓里把 autocontents-skill 转成独立 git 仓(保留文件)**

```bash
cd "G:/ai-toolkit/skills/autocontents-skill"
git init
git add -A
git status --short
```
预期:`git init` 初始化一个空仓,`git add -A` 后 `git status --short` 列出所有文件为 `A ` 状态(还没 commit)。`SKILL.md` `references/` `scripts/` `static/` 等都应列出(若这些子目录存在)。

- [ ] **Step 3: 写 CHANGELOG.md**

创建 `G:\ai-toolkit\skills\autocontents-skill\CHANGELOG.md`:
```markdown
# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-07-09

### Added
- 初始抽取为独立 SemVer 子子仓
- 来源: `G:\ai-toolkit\skills\autocontents-skill/` 主仓直管历史
```

- [ ] **Step 4: 首次 commit + SemVer tag**

```bash
cd "G:/ai-toolkit/skills/autocontents-skill"
git add -A
git commit -m "feat: initial extraction as independent SemVer sub-submodule

从主仓 G:\\ai-toolkit\\ 剥离,作为嵌套 submodule 的子子仓。独立版本号管理。
Co-Authored-By: Claude <noreply@anthropic.com>"
git tag v0.1.0
git log --oneline
```
预期:看到 1 个 commit 和 `v0.1.0` tag。

- [ ] **Step 5: 推到 bare 中转**

```bash
cd "G:/ai-toolkit/skills/autocontents-skill"
git remote add origin "../.git-remotes/skills_submodules/autocontents-skill.git"
git push origin main
git push origin v0.1.0
```
预期:两个 push 都成功(可能需要 `--set-upstream` 第一次)。

- [ ] **Step 6: 验证远端可用**

```bash
cd "G:/ai-toolkit/skills/autocontents-skill"
git ls-remote origin
```
预期:看到 `refs/heads/main` 和 `refs/tags/v0.1.0` 两个引用。

- [ ] **Step 7: 在主仓里把 autocontents-skill 变 gitlink**

```bash
cd "G:/ai-toolkit"
# 先确认主仓暂存区干净
git status --short
# 把 autocontents-skill 从主仓索引移除(保留工作树)
git rm --cached -r skills/autocontents-skill
git status --short
```
预期:`git rm --cached` 后主仓索引里没了这个目录,但 `ls skills/autocontents-skill/` 文件还在(本地还有 .git 仓)。`git status --short` 显示 `D  skills/autocontents-skill`(整目录从主仓索引删除)。

> ⚠️ **这一步先不要 commit**!后面 Task 5 会一起处理。

---

## Task 3: 抽取 mdtolatex 为子子仓

**Files:**
- Create: `G:\ai-toolkit\.git-remotes\skills_submodules\mdtolatex.git\`(bare)
- Create: `G:\ai-toolkit\skills\mdtolatex\.git\`(从主仓剥离)
- Create: `G:\ai-toolkit\skills\mdtolatex\CHANGELOG.md`
- Modify: 主仓视角下 `skills/mdtolatex/` 变 gitlink

**Interfaces:**
- Consumes: `G:\ai-toolkit\skills\mdtolatex\`(原主仓直管)
- Produces: `mdtolatex` 是独立 git 仓,有 v0.1.0 tag

- [ ] **Step 1: 创建子子仓的 bare 中转**

```bash
cd "G:/ai-toolkit/.git-remotes/skills_submodules"
git init --bare mdtolatex.git
ls mdtolatex.git/
```
预期:看到 bare 仓文件。

- [ ] **Step 2: 在主仓里把 mdtolatex 转成独立 git 仓**

```bash
cd "G:/ai-toolkit/skills/mdtolatex"
git init
git add -A
git status --short
```
预期:看到 `SKILL.md` `docs/` `examples/` `filters/` `convert_report.bat` `launch_table_ui.bat` 等已 staged。

- [ ] **Step 3: 写 CHANGELOG.md**

创建 `G:\ai-toolkit\skills\mdtolatex\CHANGELOG.md`:
```markdown
# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-07-09

### Added
- 初始抽取为独立 SemVer 子子仓
- 来源: `G:\ai-toolkit\skills\mdtolatex/` 主仓直管历史
```

- [ ] **Step 4: 首次 commit + SemVer tag**

```bash
cd "G:/ai-toolkit/skills/mdtolatex"
git add -A
git commit -m "feat: initial extraction as independent SemVer sub-submodule

从主仓 G:\\ai-toolkit\\ 剥离,作为嵌套 submodule 的子子仓。独立版本号管理。
Co-Authored-By: Claude <noreply@anthropic.com>"
git tag v0.1.0
git log --oneline
```

- [ ] **Step 5: 推到 bare 中转**

```bash
cd "G:/ai-toolkit/skills/mdtolatex"
git remote add origin "../.git-remotes/skills_submodules/mdtolatex.git"
git push origin main
git push origin v0.1.0
```

- [ ] **Step 6: 在主仓里把 mdtolatex 变 gitlink(不 commit)**

```bash
cd "G:/ai-toolkit"
git rm --cached -r skills/mdtolatex
git status --short
```
预期:看到 `D  skills/mdtolatex`(整目录从主仓索引删除),但工作树文件还在。

---

## Task 4: 抽取 md-to-docx 为子子仓

**Files:**
- Create: `G:\ai-toolkit\.git-remotes\skills_submodules\md-to-docx.git\`(bare)
- Create: `G:\ai-toolkit\skills\md-to-docx\.git\`(从主仓剥离)
- Create: `G:\ai-toolkit\skills\md-to-docx\CHANGELOG.md`
- Modify: 主仓视角下 `skills/md-to-docx/` 变 gitlink

**Interfaces:**
- Consumes: `G:\ai-toolkit\skills\md-to-docx\`(原主仓直管)
- Produces: `md-to-docx` 是独立 git 仓,有 v0.1.0 tag

- [ ] **Step 1: 创建子子仓的 bare 中转**

```bash
cd "G:/ai-toolkit/.git-remotes/skills_submodules"
git init --bare md-to-docx.git
ls md-to-docx.git/
```

- [ ] **Step 2: 在主仓里把 md-to-docx 转成独立 git 仓**

```bash
cd "G:/ai-toolkit/skills/md-to-docx"
git init
git add -A
git status --short
```
预期:看到 `SKILL.md` `scripts/` 等已 staged。

- [ ] **Step 3: 写 CHANGELOG.md**

创建 `G:\ai-toolkit\skills\md-to-docx\CHANGELOG.md`:
```markdown
# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-07-09

### Added
- 初始抽取为独立 SemVer 子子仓
- 来源: `G:\ai-toolkit\skills\md-to-docx/` 主仓直管历史
```

- [ ] **Step 4: 首次 commit + SemVer tag**

```bash
cd "G:/ai-toolkit/skills/md-to-docx"
git add -A
git commit -m "feat: initial extraction as independent SemVer sub-submodule

从主仓 G:\\ai-toolkit\\ 剥离,作为嵌套 submodule 的子子仓。独立版本号管理。
Co-Authored-By: Claude <noreply@anthropic.com>"
git tag v0.1.0
git log --oneline
```

- [ ] **Step 5: 推到 bare 中转**

```bash
cd "G:/ai-toolkit/skills/md-to-docx"
git remote add origin "../.git-remotes/skills_submodules/md-to-docx.git"
git push origin main
git push origin v0.1.0
```

- [ ] **Step 6: 在主仓里把 md-to-docx 变 gitlink(不 commit)**

```bash
cd "G:/ai-toolkit"
git rm --cached -r skills/md-to-docx
git status --short
```
预期:看到 `D  skills/md-to-docx`。

---

## Task 5: 抽取 skills/ 为子仓(含 3 个 sub-submodule 引用)

**Files:**
- Create: `G:\ai-toolkit\.git-remotes\skills.git\`(bare)
- Create: `G:\ai-toolkit\skills\.git\`(从主仓剥离,包含 7 个直管 skill + 3 个子子仓)
- Create: `G:\ai-toolkit\skills\.gitmodules`(声明 3 个 sub-submodule)
- Modify: 主仓视角下 `skills/` 变 gitlink

**Interfaces:**
- Consumes: Task 2-4 抽出的 3 个子子仓(已在 `skills/<name>/`)
- Produces: `skills/` 是独立 git 仓,内含 7 个直管 skill + 3 个 sub-submodule

- [ ] **Step 1: 创建 skills 子仓的 bare 中转**

```bash
cd "G:/ai-toolkit/.git-remotes"
git init --bare skills.git
ls skills.git/
```

- [ ] **Step 2: 在主仓里把 skills/ 转成独立 git 仓(此时已不含 3 个子子仓,因已在 Task 2-4 剥离)**

```bash
cd "G:/ai-toolkit/skills"
# 此时 skills/ 下应该还有 7 个直管 skill:
# auto-dev, auto-code-android-dev, auto-dev-check, auto-dev-resume, chatgpt-input-output, workflow-router, _shared
# 3 个子子仓(autocontents-skill, mdtolatex, md-to-docx)已有 .git/ 在本地,但 skills/ 主仓索引中已 rm --cached
ls
```
预期:看到 7 个直管目录(没有 SKILL.md 在 skills/ 根,因为 SKILL.md 在每个子 skill 内)。

- [ ] **Step 3: 在 skills/ 初始化 git 仓**

```bash
cd "G:/ai-toolkit/skills"
git init
# 3 个子子仓已经是独立 git 仓,不能 add 它们的内容
# 7 个直管 skill + _shared/ 要 add
git add auto-dev auto-code-android-dev auto-dev-check auto-dev-resume chatgpt-input-output workflow-router _shared
git status --short
```
预期:看到 7 个目录已 staged(`A ` 前缀),3 个子子仓**未** staged(因已有 .git/)。

- [ ] **Step 4: 写 skills 子仓的 .gitmodules**

创建 `G:\ai-toolkit\skills\.gitmodules`:
```ini
[submodule "autocontents-skill"]
	path = autocontents-skill
	url = ../.git-remotes/skills_submodules/autocontents-skill.git
	branch = main

[submodule "mdtolatex"]
	path = mdtolatex
	url = ../.git-remotes/skills_submodules/mdtolatex.git
	branch = main

[submodule "md-to-docx"]
	path = md-to-docx
	url = ../.git-remotes/skills_submodules/md-to-docx.git
	branch = main
```

- [ ] **Step 5: commit skills 子仓 + 推 bare**

```bash
cd "G:/ai-toolkit/skills"
git add .gitmodules
git commit -m "feat: extract skills/ as independent submodule

- 7 个直管 skill: auto-dev, auto-code-android-dev, auto-dev-check,
  auto-dev-resume, chatgpt-input-output, workflow-router, _shared
- 3 个 sub-submodule 引用: autocontents-skill, mdtolatex, md-to-docx
  (各自独立 SemVer + CHANGELOG)
- 子仓本地无远端,bare 中转在 ../../.git-remotes/skills.git

Co-Authored-By: Claude <noreply@anthropic.com>"
git remote add origin "../.git-remotes/skills.git"
git push origin main
git log --oneline
```
预期:看到 1 个 commit,push 成功。

- [ ] **Step 6: 在主仓里把 skills 变 gitlink(不 commit)**

```bash
cd "G:/ai-toolkit"
git rm --cached -r skills
git status --short
```
预期:看到 `D  skills`(整目录),但工作树里 `skills/.git/` 还在(子仓已独立)。

- [ ] **Step 7: 验证 skills 子仓和子子仓状态**

```bash
cd "G:/ai-toolkit/skills"
git status
git submodule status
```
预期:skills/ 工作树干净,3 个 sub-submodule 状态显示为正常 commit SHA(因为 .gitmodules 路径在工作树内存在,但 sub-submodule 内容是各自 .git 仓,可能需要 `git submodule init` 来注册)。如果显示 `(uninitialized)`,跑 `git submodule init` 后再 `git submodule status` 即可。

---

## Task 6: 抽取 agent-memory/ 为子仓

**Files:**
- Create: `G:\ai-toolkit\.git-remotes\agent-memory.git\`(bare)
- Create: `G:\ai-toolkit\agent-memory\.git\`(从主仓剥离)
- Modify: 主仓视角下 `agent-memory/` 变 gitlink

**Interfaces:**
- Consumes: `G:\ai-toolkit\agent-memory\`(原主仓直管)
- Produces: `agent-memory` 是独立 git 仓

- [ ] **Step 1: 创建 agent-memory 子仓的 bare 中转**

```bash
cd "G:/ai-toolkit/.git-remotes"
git init --bare agent-memory.git
ls agent-memory.git/
```

- [ ] **Step 2: 在主仓里把 agent-memory 转成独立 git 仓**

```bash
cd "G:/ai-toolkit/agent-memory"
ls
```
预期:看到 `00_inbox/` `01_globel.md` `03_agents/` `04_distilled/`(`04_distilled/` 应该被 .gitignore 忽略,但工作树存在)。

- [ ] **Step 3: 初始化 + commit agent-memory 子仓**

```bash
cd "G:/ai-toolkit/agent-memory"
git init
# 04_distilled/ 已在 .gitignore 范围(主仓 .gitignore 第 20 行: agent-memory/distilled/)
# 但 agent-memory 子仓的 .gitignore 默认未配置,需要先确认
ls -la .gitignore 2>/dev/null || echo "no local .gitignore"
```

预期:如果**没有** `agent-memory/.gitignore`,继续 Step 4 创建;如果有,继续 Step 5。

- [ ] **Step 4: 写 agent-memory 子仓的 .gitignore**

创建 `G:\ai-toolkit\agent-memory\.gitignore`:
```
# Distilled output is regenerated each run
04_distilled/

# Inbox 是临时落地区,可能不需要 track(可选,看用户偏好)
# 00_inbox/
```

> **注意**:如果决定跟踪 `00_inbox/`,把第二段注释掉。

- [ ] **Step 5: 首次 commit + 推 bare**

```bash
cd "G:/ai-toolkit/agent-memory"
git add -A
git status --short
git commit -m "feat: extract agent-memory/ as independent submodule

- 4 个区: 00_inbox/, 01_globel.md, 03_agents/, 04_distilled/(gitignore)
- 子仓本地无远端,bare 中转在 ../../.git-remotes/agent-memory.git

Co-Authored-By: Claude <noreply@anthropic.com>"
git remote add origin "../.git-remotes/agent-memory.git"
git push origin main
git log --oneline
```
预期:1 个 commit,push 成功。

- [ ] **Step 6: 在主仓里把 agent-memory 变 gitlink(不 commit)**

```bash
cd "G:/ai-toolkit"
git rm --cached -r agent-memory
git status --short
```
预期:看到 `D  agent-memory`。

---

## Task 7: 主仓 commit submodule 引用

**Files:**
- Create: `G:\ai-toolkit\.gitmodules`(主仓)
- Modify: 主仓索引,加入 2 个 gitlink

**Interfaces:**
- Consumes: Task 5、6 抽出的 skills.git 和 agent-memory.git
- Produces: 主仓引用 2 个 submodule,`git submodule status` 正常

- [ ] **Step 1: 写主仓 .gitmodules**

创建 `G:\ai-toolkit\.gitmodules`:
```ini
[submodule "skills"]
	path = skills
	url = ./.git-remotes/skills.git
	branch = main

[submodule "agent-memory"]
	path = agent-memory
	url = ./.git-remotes/agent-memory.git
	branch = main
```

- [ ] **Step 2: 注册并初始化主仓的 2 个 submodule**

```bash
cd "G:/ai-toolkit"
git submodule init
git submodule status
```
预期:看到 `skills` 和 `agent-memory` 2 个 submodule 显示为 commit SHA(已 init,但**未 update**——子仓内容已在工作树,git 知道 SHA)。如果显示 `(uninitialized)`,跑 `git submodule update` 让 git 同步 gitlink 指针。

- [ ] **Step 3: 验证嵌套结构**

```bash
cd "G:/ai-toolkit"
git submodule status
cd skills
git submodule status
```
预期:
- 主仓层:`<SHA> skills (heads/main)` 和 `<SHA> agent-memory (heads/main)`
- 子仓层:3 个 sub-submodule,每个显示为 commit SHA(可能 detached HEAD,因为是子子仓的 v0.1.0 commit)

- [ ] **Step 4: 检查主仓 git status**

```bash
cd "G:/ai-toolkit"
git status --short
```
预期:看到 `M  .gitignore` + `M  .stignore`(Task 1)+ `D  skills` + `D  agent-memory` + `?? .gitmodules`(新建未跟踪)。**3 个 `D` 行可以接受**——`git rm --cached` 已让主仓索引不含这些目录。

- [ ] **Step 5: add + commit**

```bash
cd "G:/ai-toolkit"
git add .gitmodules
# 重新检查 status
git status --short
```
预期:`D  skills` 和 `D  agent-memory` 还在(因为主仓**应该**保留 gitlink 引用,而非纯删除)。

> ⚠️ **如果显示 `D  skills` 而没有 `M  skills` (gitlink)**:说明 `git rm --cached` 把整个目录删了索引,但 git 还没识别为 submodule。需要额外执行:
> ```bash
> cd "G:/ai-toolkit"
> git add skills  # 重新以 submodule 形式 add
> git add agent-memory
> git status --short
> ```
> 应该看到 `M  skills` (submodule change) 和 `M  agent-memory`。

- [ ] **Step 6: 提交主仓重构**

```bash
cd "G:/ai-toolkit"
git commit -m "feat: restructure as nested submodule

主仓拆为嵌套 submodule 结构:
- 2 个 submodule: skills/(含 3 个 sub-submodule), agent-memory/
- 3 个 sub-submodule: autocontents-skill, mdtolatex, md-to-docx
  (各自独立 SemVer + CHANGELOG)
- 主仓仅跟踪 scripts + 4 个项目记忆 + .gitignore/.stignore/.gitmodules
- 子仓本地无远端,bare 中转在 .git-remotes/(Syncthing 排除)

详见 docs/superpowers/specs/2026-07-09-nested-submodule-restructure-design.md

Co-Authored-By: Claude <noreply@anthropic.com>"
```

- [ ] **Step 7: 验证主仓 git log 干净**

```bash
cd "G:/ai-toolkit"
git log --oneline -5
git status
```
预期:看到本次 commit 在最近 5 个之内,`git status` 干净(无 untracked/modified)。

---

## Task 8: 新增 init-submodules.ps1

**Files:**
- Create: `G:\ai-toolkit\init-submodules.ps1`

**Interfaces:**
- Consumes: 主仓 `.gitmodules` + 子仓 `.gitmodules`
- Produces: 两层 submodule 都 init/update 完毕

- [ ] **Step 1: 写 init-submodules.ps1**

创建 `G:\ai-toolkit\init-submodules.ps1`:
```powershell
<#
.SYNOPSIS
  初始化主仓 + 子仓的嵌套 submodule。

.DESCRIPTION
  跑两层 git submodule update --init --recursive:
  - 1 层: skills/ + agent-memory/(主仓 .gitmodules)
  - 2 层: autocontents-skill/ + mdtolatex/ + md-to-docx/(skills/.gitmodules)

  PC#2 首次配置 + 日常 submodule 指针更新都用这个脚本。

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\init-submodules.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# 1. 主仓层
Write-Host "==> 1/2 主仓 submodule update..." -ForegroundColor Cyan
git submodule update --init --recursive
if ($LASTEXITCODE -ne 0) { throw "主仓 submodule update 失败" }

# 2. 子仓层(嵌套)
Write-Host "==> 2/2 子仓 nested submodule update..." -ForegroundColor Cyan
Push-Location skills
try {
    git submodule update --init --recursive
    if ($LASTEXITCODE -ne 0) { throw "子仓 submodule update 失败" }
} finally {
    Pop-Location
}

Write-Host "`n✓ 两层 submodule 就绪" -ForegroundColor Green
git submodule status
Push-Location skills
try { git submodule status } finally { Pop-Location }
```

- [ ] **Step 2: 跑一次验证**

```bash
cd "G:/ai-toolkit"
powershell -ExecutionPolicy Bypass -File ./init-submodules.ps1
```
预期:输出 `==> 1/2 主仓 submodule update...` + `==> 2/2 子仓 nested submodule update...` + `✓ 两层 submodule 就绪` + 5 个 SHA(2 个主仓 + 3 个子仓层)。

- [ ] **Step 3: 验证 sub-submodule 状态**

```bash
cd "G:/ai-toolkit/skills"
git submodule status
```
预期:3 个 sub-submodule 都是 commit SHA,无 `(uninitialized)` 标记。

- [ ] **Step 4: Commit**

```bash
cd "G:/ai-toolkit"
git add init-submodules.ps1
git commit -m "feat(scripts): add init-submodules.ps1

一键跑两层 git submodule update --init --recursive(主仓 + skills/ 子仓)。
PC#2 首次配置和日常 submodule 指针更新都用这个脚本。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 9: 新增 bump-skill.ps1

**Files:**
- Create: `G:\ai-toolkit\bump-skill.ps1`

**Interfaces:**
- Consumes: 3 个子子仓路径(autocontents-skill / mdtolatex / md-to-docx)
- Produces: 子子仓 commit + SemVer tag + push,主仓和 skills/ 子仓的 submodule 引用更新

- [ ] **Step 1: 写 bump-skill.ps1**

创建 `G:\ai-toolkit\bump-skill.ps1`:
```powershell
<#
.SYNOPSIS
  3 个子子仓的 SemVer commit + tag + push 助手。

.DESCRIPTION
  用法: bump-skill.ps1 -Skill <name> [-Type major|minor|patch] [-Message <msg>]
  例子: bump-skill.ps1 -Skill autocontents-skill -Type minor -Message "新增 XX 功能"

  流程:
  1. cd 进 skills/<name>/
  2. 拉最新(bare 仓本地,无需 fetch)
  3. git add -A + commit(若工作树有改动)
  4. 计算下一个 SemVer tag(从最新 tag 解析,按 -Type 增量)
  5. git tag <new>
  6. git push origin main --follow-tags
  7. 回到 skills/ 子仓更新引用 + commit
  8. 回到主仓更新 skills/ 引用 + commit
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('autocontents-skill', 'mdtolatex', 'md-to-docx')]
    [string]$Skill,

    [ValidateSet('major', 'minor', 'patch')]
    [string]$Type = 'patch',

    [string]$Message = ''
)

$ErrorActionPreference = 'Stop'

$skillPath = Join-Path $PSScriptRoot "skills/$Skill"
if (-not (Test-Path $skillPath)) { throw "找不到子子仓: $skillPath" }

# 1. cd 进子子仓
Push-Location $skillPath
try {
    Write-Host "==> 1/4 子子仓 commit..." -ForegroundColor Cyan
    git add -A
    $commitMsg = if ($Message) { $Message } else { "chore($Skill): bump" }
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  无 staged 改动,跳过 commit" -ForegroundColor Yellow
    } else {
        git commit -m "$commitMsg`n`nCo-Authored-By: Claude <noreply@anthropic.com>"
    }

    # 2. 计算 SemVer
    Write-Host "==> 2/4 计算 SemVer..." -ForegroundColor Cyan
    $latestTag = (git tag --sort=-v:refname | Select-Object -First 1)
    if (-not $latestTag) { $latestTag = 'v0.0.0' }
    if ($latestTag -notmatch '^v(\d+)\.(\d+)\.(\d+)$') {
        throw "最新 tag 格式不对: $latestTag(需要 vX.Y.Z)"
    }
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    $patch = [int]$Matches[3]
    switch ($Type) {
        'major' { $major++; $minor = 0; $patch = 0 }
        'minor' { $minor++; $patch = 0 }
        'patch' { $patch++ }
    }
    $newTag = "v$major.$minor.$patch"
    Write-Host "  $latestTag -> $newTag" -ForegroundColor Green

    # 3. 打 tag + push
    Write-Host "==> 3/4 tag + push..." -ForegroundColor Cyan
    git tag $newTag
    git push origin main --follow-tags
} finally {
    Pop-Location
}

# 4. 回到上层更新引用
Write-Host "==> 4/4 更新上层 submodule 引用..." -ForegroundColor Cyan
Push-Location (Join-Path $PSScriptRoot 'skills')
try {
    git add $Skill
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -m "chore(skills): bump $Skill to $newTag`n`nCo-Authored-By: Claude <noreply@anthropic.com>"
        git push origin main
    } else {
        Write-Host "  skills/ 引用无变化" -ForegroundColor Yellow
    }
} finally {
    Pop-Location
}

Push-Location $PSScriptRoot
try {
    git add skills
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -m "chore: bump skills submodule ($Skill $newTag)`n`nCo-Authored-By: Claude <noreply@anthropic.com>"
    } else {
        Write-Host "  主仓引用无变化" -ForegroundColor Yellow
    }
} finally {
    Pop-Location
}

Write-Host "`n✓ $Skill bumped to $newTag" -ForegroundColor Green
```

- [ ] **Step 2: 跑一次 dry-run(改一个文件然后 bump patch)**

```bash
cd "G:/ai-toolkit/skills/autocontents-skill"
echo "" >> SKILL.md
cd "G:/ai-toolkit"
powershell -ExecutionPolicy Bypass -File ./bump-skill.ps1 -Skill autocontents-skill -Type patch
```
预期:看到 4 步进度,`v0.1.0 -> v0.1.1`,3 个 commit(子子仓 + skills/ + 主仓)。

- [ ] **Step 3: 验证最终状态**

```bash
cd "G:/ai-toolkit"
git log --oneline -3
cd skills && git log --oneline -3 && cd ..
cd skills/autocontents-skill && git log --oneline -3 && git tag
```
预期:
- 主仓:最近 commit 是 "chore: bump skills submodule"
- skills/:最近 commit 是 "chore(skills): bump autocontents-skill to v0.1.1"
- 子子仓:看到 2 个 commit 和 `v0.1.0` `v0.1.1` 两个 tag

- [ ] **Step 4: 回滚 dry-run 改动(避免污染主分支)**

```bash
# 撤销子子仓 v0.1.1 改动
cd "G:/ai-toolkit/skills/autocontents-skill"
git tag -d v0.1.1
git reset --hard v0.1.0
git push origin :v0.1.1
git push origin main --force

# 撤销 skills/ 引用更新
cd ..
git reset --hard HEAD~1
git push origin main --force

# 撤销主仓引用更新
cd ..
git reset --hard HEAD~1
```

> **注意**:如果不允许 force push 到 main(用户偏好),则跳过 reset,保留 v0.1.1 作为真实迭代;否则按上面回滚。

- [ ] **Step 5: Commit(仅新增脚本)**

```bash
cd "G:/ai-toolkit"
git add bump-skill.ps1
git commit -m "feat(scripts): add bump-skill.ps1

3 个子子仓的 SemVer commit + tag + push 助手,自动更新上层 submodule 引用。
用法: bump-skill.ps1 -Skill <name> -Type major|minor|patch -Message <msg>

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 10: 更新 README.md 和 projects.md

**Files:**
- Modify: `G:\ai-toolkit\README.md`(加 submodule 步骤)
- Modify: `G:\ai-toolkit\projects.md`(更新结构段)

- [ ] **Step 1: 在 README.md 现有"PC#1 首次配置"后追加"嵌套 submodule"段**

在 `G:\ai-toolkit\README.md` 找到 "## 日常使用" 之前的位置,插入:

```markdown
### 嵌套 Submodule 结构(2026-07-09 重构后)

主仓拆为嵌套结构:
- **主仓** = scripts + 4 个项目记忆
- **2 个 submodule**: `skills/` 整体 + `agent-memory/`
- **3 个 sub-submodule**(在 `skills/` 内): `autocontents-skill` / `mdtolatex` / `md-to-docx` 各自独立 SemVer + CHANGELOG
- **7 个 skill 在 skills/ 子仓直管**: `auto-dev` / `auto-code-android-dev` / `auto-dev-check` / `auto-dev-resume` / `chatgpt-input-output` / `workflow-router` / `_shared`

**改子子仓后的提交流程**:
```bash
# 1. 改子子仓代码
cd G:\ai-toolkit\skills\autocontents-skill
$EDITOR SKILL.md
# 2. 一键 commit + tag + push + 上层引用更新
powershell -ExecutionPolicy Bypass -File G:\ai-toolkit\bump-skill.ps1 -Skill autocontents-skill -Type minor -Message "新增 XX"
```

**手动 commit 流程**(无脚本):
```bash
# 1. 子子仓内
cd G:\ai-toolkit\skills\autocontents-skill
git add -A && git commit -m "..."
git tag v0.2.0 && git push origin main --follow-tags

# 2. skills/ 子仓更新引用
cd ..
git add autocontents-skill && git commit -m "bump" && git push

# 3. 主仓更新引用
cd ..
git add skills && git commit -m "bump skills"
```

**改 agent-memory 后的提交流程**:
```bash
cd G:\ai-toolkit\agent-memory
$EDITOR 01_globel.md
git add -A && git commit -m "..." && git push origin main
cd ..
git add agent-memory && git commit -m "bump agent-memory"
```
```

- [ ] **Step 2: 更新 README.md "PC#2 首次配置" 段**

找到 PC#2 首次配置步骤,在 "5. 跑一次 `install-all.ps1` 让各框架落盘" **之前**插入:

```markdown
4.5. 初始化嵌套 submodule(两层):
```bash
cd G:\ai-toolkit
powershell -ExecutionPolicy Bypass -File .\init-submodules.ps1
```
此脚本跑:
- 1 层:`git submodule update --init --recursive`(主仓 .gitmodules 引用 skills/ + agent-memory/)
- 2 层:`cd skills && git submodule update --init --recursive`(子仓 .gitmodules 引用 3 个 sub-submodule)
```

- [ ] **Step 3: 更新 projects.md 仓库结构段**

编辑 `G:\ai-toolkit\projects.md`,把"仓库"段更新为:

```markdown
**仓库结构**(2026-07-09 重构后,嵌套 submodule):
- `G:\ai-toolkit\` — 主仓
  - 跟踪: `install-all.ps1` / `manifest.json` / `distill-memory.ps1` / 4 个项目记忆 / `README.md` / `.gitmodules`
  - 2 个 submodule: `skills/` 整体 + `agent-memory/`
- `G:\ai-toolkit\skills\` — 子仓(独立 git)
  - 7 个直管 skill: auto-dev / auto-code-android-dev / auto-dev-check / auto-dev-resume / chatgpt-input-output / workflow-router / _shared
  - 3 个 sub-submodule: autocontents-skill / mdtolatex / md-to-docx(各自 SemVer)
- `G:\ai-toolkit\agent-memory\` — 子仓(独立 git,内含 00_inbox/01_globel.md/03_agents/04_distilled/)
- 物理中转:`G:\ai-toolkit\.git-remotes\`(本地 bare repo,Syncthing 排除)
```

- [ ] **Step 4: 更新 projects.md Phase 2 段**

在 Phase 2 列表**前面**插入新条目:

```markdown
- ✅ 仓库拆为嵌套 submodule(2026-07-09,详见 docs/superpowers/specs/2026-07-09-nested-submodule-restructure-design.md)
- ⏸️ 开机自启动检测新 commit 自动 install(用户明确暂不做)
- ...
```

- [ ] **Step 5: 验证文档无明显错位**

```bash
cd "G:/ai-toolkit"
# 简单 grep 关键段是否完整
grep -n "嵌套 Submodule" README.md
grep -n "bump-skill.ps1" README.md
grep -n "init-submodules.ps1" README.md
grep -n "嵌套 submodule" projects.md
```
预期:每行都看到 1 个匹配。

- [ ] **Step 6: Commit**

```bash
cd "G:/ai-toolkit"
git add README.md projects.md
git commit -m "docs: update README/projects for nested submodule structure

- README: 加 submodule 提交流程 + PC#2 init-submodules 步骤
- projects: 更新仓库结构段(嵌套 submodule) + Phase 2 标记完成

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 11: PC#2 端到端验证(可选,需要 Syncthing 配置好的 PC#2)

**Files:**
- Modify: PC#2 `G:\ai-toolkit\`(从 Syncthing 拉新内容)

**Interfaces:**
- Consumes: PC#1 主仓最新 commit + bare 中转仓内容
- Produces: PC#2 `git status` 干净,`/skills` 列出 9 个 skill,`install-all.ps1` 成功

> ⚠️ **此任务不 commit**(PC#2 不 commit 任何子仓)

- [ ] **Step 1: 在 PC#2 触发 Syncthing 同步**

打开 PC#2 的 Syncthing GUI (`http://localhost:8384`),等 `central-toolkit` 文件夹显示 "Up to Date"。

预期:PC#2 `G:\ai-toolkit\` 反映 PC#1 刚才的 commit(包括 `init-submodules.ps1` / `bump-skill.ps1` / 更新后的 README/projects)。

- [ ] **Step 2: 在 PC#2 跑 init-submodules.ps1**

```bash
# PC#2 上
cd "G:/ai-toolkit"
powershell -ExecutionPolicy Bypass -File ./init-submodules.ps1
```
预期:看到 `==> 1/2` 和 `==> 2/2`,输出 5 个 SHA。

- [ ] **Step 3: 验证 PC#2 嵌套状态**

```bash
cd "G:/ai-toolkit"
git submodule status
cd skills && git submodule status
```
预期:2 个主仓 submodule + 3 个 sub-submodule,均无 `(uninitialized)` / `(broken)`。

- [ ] **Step 4: 跑 install-all.ps1**

```bash
cd "G:/ai-toolkit"
powershell -ExecutionPolicy Bypass -File ./install-all.ps1
```
预期:看到所有 9 个 skill 被分发到各 framework 日志,无错误。

- [ ] **Step 5: 验证 framework 看到 skill**

```bash
# 启动 claude
claude
# 在 claude 内跑
/skills
```
预期:看到全部 9 个 skill 列出(`autocontents-skill` / `mdtolatex` / `md-to-docx` / `auto-dev` / `auto-code-android-dev` / `auto-dev-check` / `auto-dev-resume` / `chatgpt-input-output` / `workflow-router`)。

- [ ] **Step 6: 验证 PC#2 git status 干净**

```bash
cd "G:/ai-toolkit"
git status
```
预期:`nothing to commit, working tree clean`(可能显示 "modified content" 警告,因为子仓有未推送的 commit——这是正常的,只要不 `git add`)。

- [ ] **Step 7: 在 PC#2 留 verification log**

创建 `G:\ai-toolkit\install.log` 追加(PC#2):
```
=== 2026-07-09 PC#2 nested submodule verification ===
init-submodules.ps1: OK
git submodule status: 2 主仓 + 3 sub-submodule, all initialized
install-all.ps1: 9 skills distributed to N frameworks
/skills: 9 skills listed
```

- [ ] **Step 8: 把 install.log 推到 PC#1(可选)**

如果 PC#2 想要把这个 log 同步到 PC#1(Syncthing 会自动),直接在 PC#1 跑:
```bash
cd "G:/ai-toolkit"
git add install.log
git commit -m "chore: PC#2 verification log for nested submodule restructure

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Self-Review Checklist

完成后必须验证(每项独立可测):

- [ ] **Task 1**: `.git-remotes/` 存在,主仓 `.gitignore` 含 `.git-remotes/`,`.stignore` 含 `(?d).git-remotes/`
- [ ] **Task 2-4**: 3 个子子仓 `git tag` 看到 `v0.1.0`,`git ls-remote origin` 看到 main + v0.1.0
- [ ] **Task 5**: `skills/.gitmodules` 含 3 个 sub-submodule,skills 子仓有 1+ commit
- [ ] **Task 6**: `agent-memory` 子仓有 1+ commit,`04_distilled/` 被 .gitignore 排除
- [ ] **Task 7**: 主仓 `git submodule status` 2 个 submodule 状态正常,`git log` 看到重构 commit
- [ ] **Task 8**: `init-submodules.ps1` 跑完无错误,两层 SHA 都列出
- [ ] **Task 9**: `bump-skill.ps1` 跑一次 patch bump 成功(或 dry-run 验证后回滚)
- [ ] **Task 10**: README/projects 关键 grep 都能匹配
- [ ] **Task 11(可选)**: PC#2 跑完 `init-submodules` + `install-all.ps1`,`/skills` 列出 9 个

---

## Self-Review Notes

**Spec 覆盖**:
- ✅ 段 1 架构 — Task 1-7 实施
- ✅ 段 2 .gitmodules — Task 5(子仓)+ Task 7(主仓)
- ✅ 段 3 物理位置 — Task 1(.git-remotes 创建)
- ✅ 段 4 PC#1 流程 — Task 9(bump-skill.ps1 自动化)
- ✅ 段 5 PC#2 onboarding — Task 8(init-submodules.ps1)+ Task 11(验证)
- ✅ 段 6 兼容性 — 已在 spec 标注,本计划不修改 install-all.ps1 / manifest.json / distill-memory.ps1
- ✅ 段 7 迁移步骤 — Task 1-7 严格按 spec 7 步走
- ✅ 段 8 风险 — Task 1(stignore)+ Task 10(.stignore 文档)
- ✅ 段 9 验收 — Self-Review Checklist

**占位符**:已扫描,无 TBD/TODO/类似 Task N 引用

**类型/路径一致性**:
- 3 个子子仓路径:`autocontents-skill` / `mdtolatex` / `md-to-docx`(全程统一)
- 2 个子仓路径:`skills` / `agent-memory`(全程统一)
- bare 中转路径:`.git-remotes/skills.git` / `.git-remotes/agent-memory.git` / `.git-remotes/skills_submodules/<name>.git`(全程统一)
- 9 个 skill 名称:每个 Task 提到时一致

**潜在风险**:
- **Task 5 Step 5 push**:第一次 push 可能需要 `git push -u origin main`,若失败,补充 `-u` 标志
- **Task 7 Step 5 gitlink 状态**:若 `git rm --cached` 已删除索引,可能需手动 `git add skills` + `git add agent-memory` 让 git 识别为 submodule
- **Task 9 Step 4 force push**:如果用户不允许 force push,跳过回滚,保留 v0.1.1 作为真实迭代
- **Task 11 PC#2 验证**:依赖 Syncthing 已配对成功,若未配对需先完成 PC#2 首次配置
