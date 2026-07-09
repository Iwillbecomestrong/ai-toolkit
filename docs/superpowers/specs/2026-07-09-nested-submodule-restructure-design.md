# 嵌套 Submodule 仓库重构设计

**日期**: 2026-07-09
**状态**: 已批准设计,待实施
**作者**: Claude (brainstorming session)

---

## 1. 背景与动机

`G:\ai-toolkit\` 当前是单一 git 仓库,统一管理 9 个 AI 编程 framework 的 skills、plugins、agent 记忆。随着仓库增长,出现两个核心痛点:

1. **独立版本/CHANGELOG 缺失**:3 个复杂度较高的 skill(`autocontents-skill` / `mdtolatex` / `md-to-docx`)想各自跟踪 SemVer 版本,共享单一 git 仓让 changelog 难以管理。
2. **git 历史粒度太粗**:改 1 个 skill 就会让整个 `ai-toolkit` 仓的 `git log` 变乱,无法按 skill 隔离 commit。

**本次重构目标**:
- 3 个高复杂度 skill 各自独立 SemVer + CHANGELOG
- `skills/` 与 `agent-memory/` 拆为独立子仓,细粒度历史
- 保留主仓对基础设施脚本的统筹管理
- 兼容现有 Syncthing 跨 PC 同步 + `install-all.ps1` / `manifest.json` / `distill-memory.ps1`

---

## 2. 整体架构

```
G:\ai-toolkit\                       【主仓 root】 跟踪 scripts/记忆
├─ install-all.ps1                    (主仓直管)
├─ manifest.json                      (主仓直管)
├─ README.md / rules.md / lessons.md / preferences.md / projects.md
├─ distill-memory.ps1                 (主仓直管)
├─ {PROJECT_DIR}/                     (主仓直管,模板占位)
├─ .gitmodules                        (主仓直管,声明 2 个 submodule)
├─ skills/                            【子仓 ①】 (submodule)
│  ├─ .gitmodules                     (子仓直管,声明 3 个 sub-submodule)
│  ├─ autocontents-skill/             【子子仓 ②】 sub-submodule
│  ├─ mdtolatex/                      【子子仓 ②】 sub-submodule
│  ├─ md-to-docx/                     【子子仓 ②】 sub-submodule
│  ├─ auto-dev/                       (子仓直管,非 sub-submodule)
│  ├─ auto-code-android-dev/          (子仓直管)
│  ├─ auto-dev-check/                 (子仓直管)
│  ├─ auto-dev-resume/                (子仓直管)
│  ├─ chatgpt-input-output/           (子仓直管)
│  ├─ workflow-router/                (子仓直管)
│  └─ _shared/                        (子仓直管)
└─ agent-memory/                      【子仓 ①】 (submodule)
   ├─ 00_inbox/
   ├─ 01_globel.md
   ├─ 03_agents/
   └─ 04_distilled/                   (distill-memory.ps1 输出)
```

**3 层 git 实体**:
- **主仓**:仅管 scripts + 4 个项目记忆 + 模板占位 + `.gitmodules`
- **2 个子仓**:`skills/` 整体 + `agent-memory/`
- **3 个子子仓**:`autocontents-skill` / `mdtolatex` / `md-to-docx` 各自独立 SemVer

---

## 3. Submodule 配置

### 3.1 主仓 `.gitmodules`(位于 `G:\ai-toolkit\.gitmodules`)

```ini
[submodule "skills"]
    path = skills
    url  = ./skills.git
    branch = main

[submodule "agent-memory"]
    path = agent-memory
    url  = ./agent-memory.git
    branch = main
```

### 3.2 子仓 `skills/` 内的 `.gitmodules`

```ini
[submodule "autocontents-skill"]
    path = autocontents-skill
    url  = ../skills_submodules/autocontents-skill.git
    branch = main

[submodule "mdtolatex"]
    path = mdtolatex
    url  = ../skills_submodules/mdtolatex.git
    branch = main

[submodule "md-to-docx"]
    path = md-to-docx
    url  = ../skills_submodules/md-to-docx.git
    branch = main
```

### 3.3 物理位置(PC#1,本地 bare repo 模式)

- 主仓:`G:\ai-toolkit\.git\`(现有)
- 子仓 bare:`G:\ai-toolkit\.git-remotes\skills.git\` 和 `G:\ai-toolkit\.git-remotes\agent-memory.git\`
- 子子仓 bare:`G:\ai-toolkit\.git-remotes\skills_submodules\autocontents-skill.git\` 等 3 个

**为什么用 bare repo 中转**:可 `git push` 让 commit 历史可审计,工作树干净;`.stignore` 加 `(?d).git-remotes/` 让 Syncthing 不同步裸仓(仅 PC#1 需要)。

---

## 4. PC#1 提交流程

### 4.1 改某个子子仓(如 autocontents-skill)

```bash
# 1. 进入子子仓
cd G:\ai-toolkit\skills\autocontents-skill

# 2. 编辑文件
$EDITOR references/...

# 3. commit + SemVer tag(由 bump-skill.ps1 自动决定 minor/patch)
git add -A
git commit -m "feat(autocontents-skill): 描述"
git tag v0.2.0
git push origin main  # 推到 .git-remotes/skills_submodules/autocontents-skill.git

# 4. 回到 skills 子仓更新引用
cd ..
git add autocontents-skill
git commit -m "chore(skills): bump autocontents-skill to v0.2.0"
git push origin main  # 推到 .git-remotes/skills.git

# 5. 回到主仓更新 skills 引用
cd ..
git add skills
git commit -m "chore: bump skills submodule"
```

### 4.2 新增脚本 `bump-skill.ps1`(主仓根,3 个子子仓通用)

- 自动检测 `feat:` / `fix:` / `BREAKING` 前缀决定 bump 类型
- 自动 commit + tag + push 到裸仓
- 自动回退到上层 commit 指针

### 4.3 改 agent-memory/

```bash
cd G:\ai-toolkit\agent-memory
# 编辑 01_globel.md / 02_topics/ / 03_agents/<x>.md
git add -A
git commit -m "feat(memory): 描述"
git push origin main
cd ..
git add agent-memory
git commit -m "chore: bump agent-memory submodule"
```

### 4.4 改主仓脚本

```bash
cd G:\ai-toolkit
# 编辑 install-all.ps1 / manifest.json / README.md 等
git add -A
git commit -m "feat(scripts): 描述"
```

---

## 5. PC#2 Onboarding 流程

### 5.1 首次配置(接续现有 Syncthing 同步完成之后)

```bash
# 1. 拉主仓 submodule 层
cd G:\ai-toolkit
git submodule update --init --recursive

# 2. 拉子仓的 sub-submodule 层
cd skills
git submodule update --init --recursive
cd ..

# 3. 跑 install-all.ps1 装到各 framework
powershell -ExecutionPolicy Bypass -File .\install-all.ps1
```

### 5.2 新增脚本 `init-submodules.ps1`(主仓根)

```powershell
# 一键跑完两层 submodule update
git submodule update --init --recursive
Push-Location skills
try { git submodule update --init --recursive } finally { Pop-Location }
Write-Host "✓ submodule 两层就绪"
```

### 5.3 日常使用(PC#2)

- Syncthing 自动同步 PC#1 推送的文件
- PC#2 跑 `git status` 看到 submodule 指针有更新时,跑 `git submodule update --recursive` 拉新内容
- **PC#2 仍不 commit 任何子仓**(沿用现有规则,避免 Syncthing 双向冲突)

---

## 6. 兼容性影响

| 组件 | 改动 | 原因 |
|---|---|---|
| `install-all.ps1` | 无需改动 | 现有逻辑是 `Get-ChildItem skills/*/SKILL.md`,submodule 模式下文件物理位置不变 |
| `manifest.json` | 无需改动 | `skills_src: "skills"` 仍指向同一物理路径 |
| `distill-memory.ps1` | 路径调整 | 输出路径 `agent-memory/04_distilled/<x>.md`(已实际使用);`.gitignore` 已忽略该目录 |
| `README.md` | **需更新** | 加 submodule init/update 步骤,加"如何提交流程" |
| `projects.md` | **需更新** | 更新"仓库"段落,Phase 2 加迁移项 |
| `.gitignore` | **需更新** | 加 `.git-remotes/`(裸仓中转) |
| `.stignore` | **需更新** | 加 `(?d).git-remotes/`(Syncthing 排除) |

---

## 7. 迁移步骤(PC#1 only)

按依赖顺序,**每步可独立回滚**:

**Step 1**:准备裸仓中转目录
- 新建 `G:\ai-toolkit\.git-remotes\` 和 `G:\ai-toolkit\.git-remotes\skills_submodules\`
- 主仓 `.gitignore` 加 `.git-remotes/`,`.stignore` 加 `(?d).git-remotes/`

**Step 2**:把 3 个子子仓抽为独立 git repo
- 对 `autocontents-skill` / `mdtolatex` / `md-to-docx` 各做一次 `git init` + 暂存 + `git remote add origin ../.git-remotes/skills_submodules/<name>.git` + push
- 生成各自 `CHANGELOG.md` 初始 v0.1.0 entry

**Step 3**:抽取 `skills/` 为子仓
- 子仓 `git init` + 包含 7 个直管目录 + `.gitmodules` 引用 3 个 sub-submodule
- `git remote add origin ../.git-remotes/skills.git` + push
- 主仓 `git rm -r skills/` 后 `git submodule add ./skills.git skills`

**Step 4**:抽取 `agent-memory/` 为子仓
- 同样 `git init` + push 到 `.git-remotes/agent-memory.git/`
- 主仓 `git rm -r agent-memory/` 后 `git submodule add ./agent-memory.git agent-memory`

**Step 5**:主仓 `.gitmodules` 提交
- 验证嵌套结构,跑 `git submodule status` 看到 skills 和 agent-memory 正确指向
- `git add .gitmodules` + commit

**Step 6**:新增脚本 + 更新文档
- 新建 `bump-skill.ps1`、`init-submodules.ps1`
- 更新 `README.md` / `projects.md` / `.gitignore` / `.stignore`
- `git add` + commit

**Step 7**:PC#2 验证
- 在 PC#2 删除 `G:\ai-toolkit\` 重新同步
- 跑 `init-submodules.ps1` + `install-all.ps1`
- 确认 `/skills` 列出全部 9 个 skill(`_shared/` 不算 skill),`agent-memory/` 内容正确

---

## 8. 风险与缓解

| 风险 | 等级 | 缓解 | 回滚 |
|---|---|---|---|
| Syncthing 同步 `.git/` 内容导致 PC#2 仓库损坏 | 高 | `.stignore` 加 `(?d).git/` 和 `(?d).git-remotes/` | PC#2 重新同步 |
| 嵌套 submodule + 双层 .gitmodules 易出错 | 中 | `bump-skill.ps1` / `init-submodules.ps1` 收口操作;README 写明顺序 | 重新跑脚本 |
| PC#1 误在主仓直接 `git add skills/<name>/...` | 中 | 加 pre-commit hook 检查 `git diff --cached` 不含 `skills/<name>/` 文件内容(submodule 引用不受 .gitignore 约束) | `git rm --cached` 还原 |
| agent-memory 移动后历史丢失 | 低 | 迁移前 `git log --all` 备份关键 commit SHA 到 `CHANGELOG.md` | 主仓 `git rm agent-memory` + 还原旧结构 |
| `install-all.ps1` 在 PC#2 跑时找不到 SKILL.md | 中 | `init-submodules.ps1` 是 `install-all.ps1` 的前置检查 | `git submodule update --init --recursive` 后重跑 |

---

## 9. 验收标准

迁移完成后必须满足:

- [ ] `G:\ai-toolkit\git submodule status` 显示 2 个 submodule,均无 `(broken)` 标记
- [ ] `G:\ai-toolkit\skills\git submodule status` 显示 3 个 sub-submodule
- [ ] 3 个子子仓各有 `CHANGELOG.md` 和至少一个 SemVer tag
- [ ] 跑 `install-all.ps1` 后,`/skills` 列出全部 9 个 skill(`_shared/` 不算 skill)
- [ ] `distill-memory.ps1` 仍能生成 `agent-memory/04_distilled/<x>.md`
- [ ] PC#2 跑 `init-submodules.ps1` 一键完成两层 init
- [ ] `.stignore` 包含 `(?d).git/` 和 `(?d).git-remotes/`
- [ ] PC#2 `git status` 干净,不报 `modified content` / `untracked` 错误

---

## 10. 后续可考虑(YAGNI,本次不做)

- 每个子仓独立 GitHub 远端托管(目前纯本地)
- 自动化 changelog 生成(从 commit message 解析)
- 子仓版本自动同步到 `manifest.json` 字段
- hook 检查"PC#1 禁止在主仓直接 add skills/ 下文件"
