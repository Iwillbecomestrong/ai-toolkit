# ai-toolkit 大本营整理 + 可程序化提取 — Design Spec

**Date**: 2026-07-14
**Status**: Draft (待 user review)
**Author**: Claude (brainstorming session with user)

## 1. 背景 / 问题陈述

`G:\ai-toolkit\agent-memory\` 是所有 framework memory 的大本营。当前 `distill-memory.ps1` 用 simple-concat 把 `01_globel.md + 03_agents/<x>.md` 推到 `~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/.gemini/GEMINI.md`。

3 个问题：

1. **`01_globel.md` 84 行偏重**：里面塞了 framework-specific 的细节（cache 红线虽然跨 framework，但分发黑名单 5 条里 3 条是 claude/codex specific；应该按 framework 维度分流到 `03_agents/`）
2. **`03_agents/claude.md` 208 行里 ~150 行是 in-flight backlog**：Q-14、Q-15、context-status 改写候选 — 是未来需求，不是当前 rules。会被 distill 推到 `~/.codex/AGENTS.md`（已发生），framework 启动读到一堆"下批要做"很迷惑
3. **可程序化知识散落**："claude 调 codex cli" 知识在 3 处（codex.md 文字 + `_codex-runtime.ps1` + 3 个 role 脚本）；"查上下文窗口" 有 3 个分散 user-level 工具（`claude-ctx` / `codex-thread-ctx` / `context-status`），3 种算法不一致（per-turn / pay-as-you-go cumulative / byte 估算 bug）

## 2. 目标

- 让 `agent-memory/01_globel.md` 真正"全局且简洁"，**~30 行**
- 把 in-flight backlog 从 `03_agents/claude.md` 物理剥出，进新建 `05_backlog/` 目录
- 抽 3 个稳定 skill 源（双形态：SKILL.md + scripts/）：
  - `skills/claude-ctx/` — per-turn 算法收口
  - `skills/codex-ctx/` — pay-as-you-go + cumulative 算法
  - `skills/codex-bridge/` — claude 调 codex cli 的稳定入口
- 修 `distill-memory.ps1`：加 `-SkipBacklog` 默认开，让 `05_backlog/` 不进 distill
- 修 `skills/_shared/scripts/show_session_context.py`：并入 `skills/claude-ctx/scripts/claude-ctx.py`，算法改 per-turn

## 3. 非目标（这次不做）

- **codex → claude 反向 bridge**：codex CLI 没有成熟的 sub-agent dispatch 机制，硬塞会拖大 scope。进 `05_backlog/codex-reverse-bridge.md` 标 future work
- **立即 Apply 到 framework prefix**（`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` / `~/.gemini/GEMINI.md`）：cache 红线要求单独 user 拍板
- **重写 `install-all.ps1`**：现有 additive 模式已够用，不动
- **新建 `02_topics/`**：当前不存在，但本次不需要（30 行极简后 globel 已经够短）

## 4. 设计

### 4.1 架构 / 文件布局

```
G:\ai-toolkit\
├── agent-memory/
│   ├── 01_globel.md                       改：84 → 30 行
│   ├── 03_agents/
│   │   ├── claude.md                      改：208 → ~70 行
│   │   ├── codex.md                       改：62 → ~30 行
│   │   ├── gemini.md                      保持
│   │   ├── copilot.md                     保持
│   │   └── aionui/codewhale/mimo/moltbot/qoder.md  保持
│   ├── 04_distilled/                      自动更新
│   ├── 00_inbox/                          保持
│   └── 05_backlog/                        新建
│       ├── skill-meta-q14.md              从 claude.md 剥
│       ├── skill-meta-q15.md              从 claude.md 剥
│       ├── context-status-rewrite.md      从 claude.md 剥
│       └── codex-reverse-bridge.md        标 future work
├── skills/
│   ├── claude-ctx/                        新建（双形态）
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── claude-ctx.py              per-turn 算法
│   │   └── tests/
│   │       └── test_claude_ctx.py
│   ├── codex-ctx/                         新建（双形态）
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── codex-ctx.py               pay-as-you-go + cumulative
│   │   └── tests/
│   │       └── test_codex_ctx.py
│   └── codex-bridge/                      新建（双形态，单向 claude→codex）
│       ├── SKILL.md
│       └── scripts/
│           ├── _codex-runtime.ps1         从 auto-code-android-dev 搬
│           ├── run-codex-plan.ps1
│           ├── run-codex-review.ps1
│           └── run-codex-implement.ps1
├── skills/_shared/
│   └── scripts/
│       └── show_session_context.py        改：算法 → per-turn，功能并入 claude-ctx.py
└── distill-memory.ps1                     改：加 -SkipBacklog 默认开
```

### 4.2 数据流 / 调用关系

```
user 在 REPL 输入 /claude-ctx
    ↓
Claude Code 加载 skills/claude-ctx/SKILL.md（description 匹配触发）
    ↓
SKILL.md 指示：跑 python3 scripts/claude-ctx.py
    ↓
claude-ctx.py 读 ~/.claude/projects/<id>/*.jsonl 最新一个
    ↓
按 per-turn 算法算 input + cache_create + cache_read + output + pay-as-you-go
    ↓
stdout 给 user（per-turn 占窗口% / 缓存命中率 / pay-as-you-go 累计）

（codex-ctx / codex-bridge 同模式）
```

**关键点**：
- skill = model-driven trigger（description 匹配）
- scripts/ = deterministic implementation（pipeline / automation 可直接调，不依赖 model 决策）
- 双形态让 user 既能 `/claude-ctx` 触发，也能直接 `python3 scripts/claude-ctx.py` 跑

### 4.3 算法收口（核心）

| 工具 | 算法 | 收口后位置 |
|---|---|---|
| `claude-ctx` | per-turn input + cache_create + cache_read | `skills/claude-ctx/scripts/claude-ctx.py` |
| `codex-ctx` | pay-as-you-go = input - cached + output + reasoning | `skills/codex-ctx/scripts/codex-ctx.py` |
| `context-status` | byte 估算（已坏，废除）| 源删除；保留 alias `.md` 文件 → 重定向到 claude-ctx |
| `show_session_context.py`（_shared 里）| sum 算法（over-counting，已坏）| 重写为 per-turn；功能并入 claude-ctx.py |

**统一规约**（写进 `01_globel.md` §lessons）：

```
per-turn 占窗口   = input_delta + cache_create_delta + cache_read_delta   (当前 turn 实占)
cumulative 占窗口 = sum(input) + sum(cache_create) + sum(cache_read)     (可超 1M, 仅 budget 报告)
pay-as-you-go     = cumulative input - cumulative cached + output + reasoning
```

### 4.4 `distill-memory.ps1` 改动

加 1 个 switch：

```powershell
[switch]$SkipBacklog = $true   # 默认开 — 05_backlog/ 不进 distill
```

main loop 前扫 `agent-memory/05_backlog/`，base name 加入 skip 列表（不读、不写到 `04_distilled/`、不推到 framework prefix）。其它逻辑不变。

向后兼容：`-SkipBacklog:$false` 强制关闭（基本不会用，留着给 debug）。

### 4.5 错误处理 / 边界 case

| 场景 | 行为 | exit code |
|---|---|---|
| `~/.claude/projects/<id>/*.jsonl` 损坏 / 不存在 | stderr 提示 + 建议跑 `/context` fallback | 2 |
| `~/.codex/sessions/.../*.jsonl` 损坏 / 不存在 | stderr 提示"没找到 session" | 1 |
| framework 未装（没 `~/.codex/AGENTS.md`）| distill 跳过（已支持）| 0 |
| `_codex-runtime.ps1` 找不到 codex cli | stderr 提示 `which codex` + 安装链接 | 3 |
| `05_backlog/` 不存在 | distill 不报错，正常运行 | 0 |
| user-level skill 引用了已删脚本 | 保留 alias `.md` 文件指向新 skill | 0 |

### 4.6 测试 / 验证

每个新 script 配 1 个 test：

- `skills/claude-ctx/tests/test_claude_ctx.py` — 用 fixture jsonl（真实 `~/.claude/projects/.../<uuid>.jsonl` 副本脱敏）跑 per-turn 算法，断言 4 项指标（input / cache_create / cache_read / output / pay-as-you-go）
- `skills/codex-ctx/tests/test_codex_ctx.py` — 同（fixture 用 `~/.codex/sessions/2026/MM/DD/rollout-*.jsonl` 副本）
- `skills/codex-bridge/tests/test_codex_bridge.ps1` — Pester-style，验证 `_codex-runtime.ps1` 找不到 codex cli 时退出码 = 3

**测试 model 选型（2026-07-14 user 立）**：
- 测试 codex 调用统一用 **default model = gpt5.4-mini**（不要 `-m gpt-5.5`）
- production call 才用 gpt-5.5 + high effort
- 避免测试浪费 gpt-5.5 quota

Acceptance 标准：

| 指标 | 阈值 |
|---|---|
| `01_globel.md` 行数 | ≤ 32 |
| `03_agents/claude.md` 行数 | ≤ 75 |
| `03_agents/codex.md` 行数 | ≤ 35 |
| `distill-memory.ps1 -List` 输出 | 多 1 行 `[05_backlog]` 标记 |
| `pytest skills/*/tests/` | 全绿 |
| `distill-memory.ps1`（无 `-Apply`）跑通 + `grep -l "Q-14\|Q-15\|context-status 改写"` `04_distilled/codex.md` | 无匹配 |
| `05_backlog/` 存在且含 4 文件 | yes |

## 5. 文件清单（精确清单）

### 改（5 个）
- `agent-memory/01_globel.md` — 84 → 30 行
- `agent-memory/03_agents/claude.md` — 208 → ~70 行（剥 Q-14/Q-15/context-status 改写到 05_backlog/）
- `agent-memory/03_agents/codex.md` — 62 → ~30 行（剥"拿 token 数据的方法"到引用 codex-ctx skill）
- `distill-memory.ps1` — 加 `-SkipBacklog` switch + main loop skip 逻辑
- `skills/_shared/scripts/show_session_context.py` — 算法改 per-turn；功能并入 `claude-ctx.py`（保留文件作为 backward-compat shim 调 claude-ctx.py）

### 新建（1 目录 + 17 文件）
- `agent-memory/05_backlog/` 目录
- `agent-memory/05_backlog/skill-meta-q14.md`
- `agent-memory/05_backlog/skill-meta-q15.md`
- `agent-memory/05_backlog/context-status-rewrite.md`
- `agent-memory/05_backlog/codex-reverse-bridge.md`
- `skills/claude-ctx/SKILL.md`
- `skills/claude-ctx/scripts/claude-ctx.py`
- `skills/claude-ctx/tests/test_claude_ctx.py`
- `skills/codex-ctx/SKILL.md`
- `skills/codex-ctx/scripts/codex-ctx.py`
- `skills/codex-ctx/tests/test_codex_ctx.py`
- `skills/codex-bridge/SKILL.md`
- `skills/codex-bridge/scripts/_codex-runtime.ps1`
- `skills/codex-bridge/scripts/run-codex-plan.ps1`
- `skills/codex-bridge/scripts/run-codex-review.ps1`
- `skills/codex-bridge/scripts/run-codex-implement.ps1`

### user-level 文件 — **本次不手动 Edit**
- `~/.claude/commands/claude-ctx.md`、`~/.claude/commands/context-status.md`、`~/.agents/skills/codex-thread-ctx/` 等已 deployed 的 user-level 文件 **不直接改**
- 由 `install-all.ps1` 走 standard install 流程装新 skill 源覆盖；deploy 时机单独 ping user（cache 红线）
- 旧 `context-status.md`（byte 估算）如果要被保留为 alias，需在 deploy 时单独 Edit 加 `# DEPRECATED: use /claude-ctx instead` 注释；本次 spec 不动它

### 搬（不删原文件，加引用）
- `skills/auto-code-android-dev/scripts/_codex-runtime.ps1` **复制**到 `skills/codex-bridge/scripts/`；原文件加 1 行 `# DEPRECATED: 详见 skills/codex-bridge/`

## 6. 风险 / 边界

| 风险 | 等级 | 缓解 |
|---|---|---|
| 改 `~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` invalidate cache | MEDIUM | **不 Apply**，只改源 + 写到 `04_distilled/`；user review 后单独 ping 才 Apply |
| 新 skill 装到 `~/.agents/skills/` 也 invalidate cache | LOW | 装到 user-level（不进 prompt prefix），影响小；3 个 skill 一起装减少 invalidate 次数 |
| `claude-ctx.py` 算法 vs 现有 user-level `~/.claude/commands/claude-ctx.md` 不一致 | LOW | 新算法是 user 验证的 per-turn；user-level 文件下次 install 会覆盖 |
| `show_session_context.py` 改算法破坏依赖它的 dispatch.ps1 | LOW | dispatch.ps1 用 init/print/record subcommand，不依赖具体算法；改后功能等价 |
| `05_backlog/` 文件名约定不清，未来容易误推 | LOW | distill-memory.ps1 加 hard skip；spec 在 §4.4 写明 |

## 7. 实施步骤（high-level）

> 详细 plan 由 writing-plans skill 出

1. **Step 1**: 建 `05_backlog/` + 剥 backlog 段落（4 文件）
2. **Step 2**: 精简 `01_globel.md` 84 → 30 行（只留 5 条 + Why/How 1 行说明）
3. **Step 3**: 精简 `03_agents/claude.md` 208 → 70 行（剥 backlog 后只留真 rules）
4. **Step 4**: 精简 `03_agents/codex.md` 62 → 30 行（剥 token 数据方法 → 引用 codex-ctx）
5. **Step 5**: 修 `distill-memory.ps1` 加 `-SkipBacklog` switch
6. **Step 6**: 新建 `skills/claude-ctx/`（SKILL.md + claude-ctx.py + test）
7. **Step 7**: 新建 `skills/codex-ctx/`（SKILL.md + codex-ctx.py + test）
8. **Step 8**: 新建 `skills/codex-bridge/`（SKILL.md + 4 个 .ps1）
9. **Step 9**: 修 `skills/_shared/scripts/show_session_context.py`（改 per-turn 算法或标 deprecated）
10. **Step 10**: 跑 `distill-memory.ps1`（无 `-Apply`），验证 `04_distilled/codex.md` 不含 Q-14/Q-15
11. **Step 11**: 跑 `pytest skills/*/tests/` 全绿
12. **Step 12**: git commit（不进 `-Apply`，新 skill 也不 install — 单独 ping user 拍板）

## 8. 关联

- **R-8** 主编排不 Edit skill 系统层 — 本次走 dist/spec 流程，不直接 Edit 已 deployed 的 user-level skill
- **cache 红线**（`01_globel.md` §"⚠ 缓存红线"）：所有 framework prefix 写入必须 user 单独拍板
- **install-all.ps1** 用 additive 模式 — 新 skill 装上不会破坏现有
- **R-7**（auto-dev pipeline skip this layer）：本次是记忆 + skill 整理，不是 task pipeline

## 9. 命名（spec 自洽）

- **task_id**: `ai-toolkit-memory-cleanup-and-program-extract-2026-07-14`
- **category**: `category-memory-cleanup-program-extract`
- **沉淀目录**: `docs/superpowers/specs/2026-07-14-ai-toolkit-memory-cleanup-and-program-extract-design.md`（即本文件）
- **dispatch label**: 无（不是 task pipeline，是 manual 整理）