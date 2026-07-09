# PLAN — skill-meta-tdd-flow — Skill 系统元改造:完整 flow 补完

> **Plan 作者**: [planner:deepseekV4pro]
> **Plan 时间**: 2026-07-09
> **类别**: pipeline-skill-change-20260709
> **Plan 版本**: v1.0.0
> **项目根**: `G:\ai-toolkit\`

---

## 1. 任务概述(需求重述 + 验收标准)

### 背景

主编排者在 `G:\ai-toolkit\skills\` (skill 系统自身)做了十几处 partial 改动,但未走 TDD + reviewer 完整流程。当前状态如下:

| 改动项 | 状态 | 文件 |
|---|---|---|
| §0 主编排禁令 + §0.5 角色映射 + §0.6 TDD/reviewer 硬规则 + §0.6.4 流程串行 + §0.7 DS-out→CODEX-review | 已写(新 section) | `_shared/SKILL_CORE.md` |
| dispatch.ps1 统一 Bash 入口 | 已创建 | `_shared/scripts/dispatch.ps1` |
| claude-developer.md / claude-tester.md / claude-researcher.md | 已创建 | `auto-dev/agents/` |
| Gate 6 模型白名单 + Gate 7 dispatch audit + posttooluse handle + handle_stop block | **未改** | `_shared/scripts/auto_dev_guard.py` |
| PostToolUse hook 注册 | **未加** | `_shared/hooks.claude.json` |
| gpt-5.4 → gpt-5.5 (Codex 脚本) | **未改** | `auto-code-android-dev/scripts/_codex-runtime.ps1` / `run-codex-*.ps1` |
| gpt-5.4 → gpt-5.5 (WORKFLOW.md) + 语义变更 | **未改** | `_shared/WORKFLOW.md` |
| gpt-5.4 → gpt-5.5 (模板) | **未改** | `_shared/templates/PLAN_AGENT_SELECTION.md` / `MODEL_QUOTA_CHECK.md.template` |
| docs/<skill>/<YYYY-MM-DD-task>/ 路径约定 | **未加** | `auto-code-android-dev/SKILL.md` |
| show_session_context.py model=/effort= 字段 | **未改** | `_shared/scripts/show_session_context.py` |
| SKILL_CORE.md §5.2 旧模型名称残余 | **残留** | `_shared/SKILL_CORE.md` |
| SKILL_CORE.md gpt-5.4 残余引用 | **残留** | `_shared/SKILL_CORE.md` |

### 改造目标

1. **补完所有未完成的 partial 改动**,使其与 SKILL_CORE.md §0-§0.7 的新规则一致
2. **验证 auto_dev_guard.py 的 Gate 6 / Gate 7 / PostToolUse / Stop 逻辑**能正确阻断/enforce
3. **统一 gpt-5.5** 为 Codex 默认模型,消除 gpt-5.4 残余,WORKFLOW.md 中"首轮 5.4 / 返工 5.5"语义替换为"统一 gpt-5.5 + effort 分层 high/xhigh"
4. **全部改完后走完整 §0.7 流程**: planner→PLAN_REVIEW→TEST_TARGET→develop→test→review→ACCEPTANCE

### 验收标准(逐条可验证)

| # | 标准 | 验证方式 |
|---|---|---|
| AC1 | 主编排 Edit/Write 命中源码白名单路径时,Gate 1/1.5 在 active task 内阻断 | 手工 scen_test: mock hook_input `{"tool_name":"Write","file_path":"src/main/Foo.kt"}`,当前 pipeline state=计划,验证 deny |
| AC2 | 派 `[planner:deepseekV4pro]` 时 Gate 7 echo `[dispatch] 派 [planner:deepseekV4pro] model=deepseekV4pro effort=max :: <task>`,落盘 `AGENT_REGISTRY.json dispatches[]` | 手工或 mock 触发 Agent tool,检查 stdout 含 `[dispatch]` 且 `AGENT_REGISTRY.json` 新增 `dispatches[]` 条目 |
| AC3 | 派 `[reviewer:codex]` 走 `dispatch.ps1 -Action codex-review -Effort high`,`CURRENT_CODEX_RUN.json` 含 `model=gpt-5.5,effort=high,session=<sid>`,dispatch.ps1 转发前 echo `[dispatch]` | `pwsh -File dispatch.ps1 -Action codex-review ...` 观察 stdout 第一行 + 检查 `CURRENT_CODEX_RUN.json` 字段 |
| AC4 | Gate 6 拒绝 `model=sonnet/opus/haiku` | mock hook_input `{"tool_name":"Agent","subagent_type":"developer","model":"sonnet"}`,验证 deny |
| AC5 | PostToolUse 检测 sub-agent 返回时,从 `tool_response` 抓 `AGENT_SESSION:` 行回填 `sub_session_id` | 派 developer 子 agent 返回后,检查 `AGENT_REGISTRY.json` 对应 dispatch record 的 `sub_session_id` 字段非 null |
| AC6 | Stop hook 在 `current_phase != done/blocked` 时返回 `decision: block` + reason 含下一步必须 dispatch 谁 | mock Stop hook_input,验证 `{"continue":false,"reason":"..."}` 而非 `{"continue":true,...}` |
| AC7 | PostToolUse hook 在 developer agent 返回时 emit "立即派 tester,不可并行派 reviewer" | 派 developer 返回后,检查 PostToolUse stdout/log 含此提示 |
| AC8 | `install-agents.ps1` 后 `~/.claude/agents/` 有 `claude-developer.md` / `claude-tester.md` / `claude-researcher.md`,且 `name:` 字段分别为 `developer` / `tester` / `researcher` | 跑 `pwsh -File G:\ai-toolkit\skills\auto-dev\scripts\install-agents.ps1`,检查目标目录文件存在 + frontmatter `name` 字段 |
| AC9 | `show_session_context.py print` 输出含 `model=<X> effort=<Y>` | `python show_session_context.py print <registry> <sid>` 检查输出行含 `model=minimax effort=high` 等 |
| AC10 | `WORKFLOW.md` 中不再有 gpt-5.4 字符串(旧模板除外),且"首轮 5.4 / 返工 5.5"语义已替换为"统一 gpt-5.5 + effort 分层" | `grep -i "gpt-5.4" WORKFLOW.md` 返回 0 结果 |
| AC11 | Codex runner 脚本默认 `$Model = 'gpt-5.5'`,prompt 文本 "Default assumption: Codex A/B/C use gpt-5.4" → "use gpt-5.5" | `grep "gpt-5.4" run-codex-*.ps1 _codex-runtime.ps1` 返回 0 结果 |
| AC12 | `MODEL_QUOTA_CHECK.md.template` 模型表不再包含 sonnet/opus/haiku | grep sonnet/opus/haiku 返回 0(或仅出现在"不可用/禁用"上下文中) |

---

## 2. 类别分组与执行顺序

### CAT-1: 核心门禁补完(auto_dev_guard.py + hooks.claude.json)

**优先级: P0(所有后续改动都依赖门禁 enforce)**

- Gate 6 白名单更新: `KNOWN_AUTO_DEV_AGENT_TYPES` 加入 `deepseek-planner` / `deepseek-reviewer` / `developer` / `tester` / `researcher`;拒绝 `model=sonnet/opus/haiku` 的错误消息改为本环境语境
- Gate 7 新增: 每次 Agent dispatch 前 echo `[dispatch] 派 [role:model] model=<X> effort=<Y>` + 落盘 `AGENT_REGISTRY.json dispatches[]`
- `handle_posttooluse` 新增: PostToolUse hook,检测 sub-agent 返回,抓 `AGENT_SESSION:` 行回填 `sub_session_id`,emit "下一步必须派 X"
- `handle_stop` 更新: active task `current_phase` 不是 `done`/`blocked` 时返回 `decision: block`(不是 allow+warnings)
- hooks.claude.json: 添加 `PostToolUse` hook section,匹配 agent 返回
- SKILL_CORE.md §5.2 旧模型名称残余清理: 所有 sonnet/opus/haiku 引用替换为 minimax/fable/deepseek 当前可用模型

**依赖**: 无(独立)

### CAT-2: gpt-5.4 → gpt-5.5 全局替换 + 语义变更

**优先级: P1(模型名统一是这次改造的核心)**

含以下文件:
- `auto-code-android-dev/scripts/_codex-runtime.ps1` (line 312: `$Model = 'gpt-5.4'` → `'gpt-5.5'`)
- `auto-code-android-dev/scripts/run-codex-plan.ps1` (line 15: 默认 Model + line 58: prompt 文本)
- `auto-code-android-dev/scripts/run-codex-review.ps1` (line 9: 默认 Model + line 64: prompt 文本)
- `auto-code-android-dev/scripts/run-codex-implement.ps1` (line 6: 默认 Model)
- `_shared/WORKFLOW.md` (所有 gpt-5.4 → gpt-5.5; 语义变更: "首轮 gpt-5.4 / 返工 gpt-5.5" → "统一 gpt-5.5 + effort 分层 high/xhigh")
- `_shared/SKILL_CORE.md` (残留 gpt-5.4 引用 → gpt-5.5; 残留旧模型名)
- `_shared/templates/PLAN_AGENT_SELECTION.md` (JSON 示例 `gpt-5.4` → `gpt-5.5`)
- `_shared/templates/MODEL_QUOTA_CHECK.md.template` (gpt-5.4→gpt-5.5 + 旧模型名替换为当前环境可用)

**依赖**: 可独立进行(纯文本替换),但与 CAT-1 的 SKILL_CORE.md §5.2 清理有重叠,建议 CAT-1 先完成 SKILL_CORE.md 部分再 CAT-2 交叉检查

### CAT-3: auto-code-android-dev SKILL.md 路径约定 + 清理

**优先级: P2(小改动)**

- 添加 §0.5: `docs/<skill>/<YYYY-MM-DD-task>/` 为 project 侧 plan / 报告沉淀路径
- 删除 line 107 的过期 TODO: "给 run-codex-*.ps1 + _codex-runtime.ps1 补 -Effort→codex exec --effort 透传"(此功能已在 feat(codex-scripts)27d70be 实现)

**依赖**: 无(独立)

### CAT-4: show_session_context.py model/effort 字段补全

**优先级: P2(小改动)**

- `cmd_init` 新增 `--effort` 参数支持
- `cmd_print` 输出行追加 `model=<X> effort=<Y>` 字段

**依赖**: 无(独立)

### CAT-5: 集成验证 + 一致性审计

**优先级: P3(串联所有改动)**

- 跑 `install-all.ps1` + `install-agents.ps1` 验证安装
- 全量 grep 确认无 `gpt-5.4` / `sonnet` / `opus` / `haiku` 残余(除禁用说明上下文外)
- `python auto_dev_guard.py pretooluse <state_dir>` 带 mock input 验证所有 Gate
- `show_session_context.py print` 验证模型名+effort 字段输出

**依赖**: CAT-1, CAT-2, CAT-3, CAT-4 全部完成

### 执行顺序

```
CAT-1 (auto_dev_guard.py + hooks.claude.json + SKILL_CORE.md §5.2 清理)
  └─→ CAT-2 (gpt-5.4 → gpt-5.5 全局替换,可与 CAT-3/4 并行)
       CAT-3 (auto-code-android-dev SKILL.md 路径约定)
       CAT-4 (show_session_context.py model/effort)
           └─→ CAT-5 (集成验证)
```

- CAT-1 和 CAT-2 中的 SKILL_CORE.md 修改有重叠,建议 CAT-1 先改 SKILL_CORE.md,然后 CAT-2 做余下的 gpt-5.4 残余清理
- CAT-3 和 CAT-4 与 CAT-2 无文件冲突,可并行

---

## 3. 影响模块与精确候选文件

### 必须修改的文件(按类别)

| 文件(绝对路径) | 所属类别 | 改动类型 | 说明 |
|---|---|---|---|
| `G:\ai-toolkit\skills\_shared\scripts\auto_dev_guard.py` | CAT-1 | 修改 | Gate 6/7 + posttooluse + handle_stop |
| `G:\ai-toolkit\skills\_shared\hooks.claude.json` | CAT-1 | 修改 | 加 PostToolUse matcher |
| `G:\ai-toolkit\skills\_shared\SKILL_CORE.md` | CAT-1+CAT-2 | 修改 | §5.2 旧模型名清理 + gpt-5.4 残余 |
| `G:\ai-toolkit\skills\auto-code-android-dev\scripts\_codex-runtime.ps1` | CAT-2 | 修改 | 默认 Model + prompt 文本 |
| `G:\ai-toolkit\skills\auto-code-android-dev\scripts\run-codex-plan.ps1` | CAT-2 | 修改 | 默认 Model + prompt 文本 |
| `G:\ai-toolkit\skills\auto-code-android-dev\scripts\run-codex-review.ps1` | CAT-2 | 修改 | 默认 Model + prompt 文本 |
| `G:\ai-toolkit\skills\auto-code-android-dev\scripts\run-codex-implement.ps1` | CAT-2 | 修改 | 默认 Model |
| `G:\ai-toolkit\skills\_shared\WORKFLOW.md` | CAT-2 | 修改 | gpt-5.4→5.5 + 语义变更 |
| `G:\ai-toolkit\skills\_shared\templates\PLAN_AGENT_SELECTION.md` | CAT-2 | 修改 | JSON 示例 gpt-5.4→5.5 |
| `G:\ai-toolkit\skills\_shared\templates\MODEL_QUOTA_CHECK.md.template` | CAT-2 | 修改 | gpt-5.4→5.5 + 模型名替换 |
| `G:\ai-toolkit\skills\auto-code-android-dev\SKILL.md` | CAT-3 | 修改 | 加 §0.5 docs 路径 + 删过期 TODO |
| `G:\ai-toolkit\skills\_shared\scripts\show_session_context.py` | CAT-4 | 修改 | cmd_print 加 model/effort; cmd_init 支持 --effort |

### 只读确认文件(不修改)

| 文件(绝对路径) | 用途 |
|---|---|
| `G:\ai-toolkit\skills\_shared\scripts\dispatch.ps1` | 参考 Gate 7 派单格式 + 模型默认值(gpt-5.5) |
| `G:\ai-toolkit\skills\auto-dev\agents\claude-developer.md` | 验证 frontmatter `name: developer` |
| `G:\ai-toolkit\skills\auto-dev\agents\claude-tester.md` | 验证 frontmatter `name: tester` |
| `G:\ai-toolkit\skills\auto-dev\agents\claude-researcher.md` | 验证 frontmatter `name: researcher` |
| `G:\ai-toolkit\skills\auto-dev\scripts\install-agents.ps1` | 参考安装逻辑 |
| `G:\ai-toolkit\skills\_shared\REPORT_FORMATS.md` | 确认 AGENT_ROLE/AGENT_SESSION/NEXT_AGENT 字段格式 |

### 新创建文件(PLAN 产出,不是源码)

| 文件(绝对路径) | 说明 |
|---|---|
| `G:\ai-toolkit\docs\auto-dev\2026-07-09-skill-meta-tdd-flow\PLAN.md` | 本文件 |
| `G:\ai-toolkit\docs\auto-dev\2026-07-09-skill-meta-tdd-flow\plan.meta.json` | PLAN 元数据 |

---

## 4. 有序实现任务与依赖

### CAT-1: 核心门禁补完

| Step | 描述 | 角色 | 文件 | 前置 |
|---|---|---|---|---|
| S1.1 | Gate 6 白名单更新: 扩展 `KNOWN_AUTO_DEV_AGENT_TYPES` 加入 `deepseek-planner`/`deepseek-reviewer`/`developer`/`tester`/`researcher`;错误消息改为 "本环境仅支持: minimax, fable (deepseek-v4-pro); Codex 走 Bash dispatch.ps1。sonnet/opus/haiku 不可用。" | developer | `auto_dev_guard.py` | — |
| S1.2 | Gate 7 新增: 在 `handle_pretooluse` 中 Agent tool 为非已知 auto-dev 类型时注入 dispatch audit echo(写到 stderr 或 return JSON extra 字段);`AGENT_REGISTRY.json` 新 record `dispatches[]` 写入 model/effort/timestamp/task | developer | `auto_dev_guard.py` | S1.1 |
| S1.3 | `handle_posttooluse` 新增: 解析 `tool_response` 找 `AGENT_SESSION:` 行 → 回填 `AGENT_REGISTRY.json dispatches[N].sub_session_id`;检测 developer agent 返回 → emit "下一步必须派 tester,不可并行派 reviewer";检测 any agent 返回 → emit "下一阶段必须派 X(不可派 Y)" | developer | `auto_dev_guard.py` | S1.2 |
| S1.4 | `handle_stop` 更新: 当 active task `current_phase` 不是 `done`/`blocked` 时,返回 `{"continue":false,"reason":"active task 未完成,下一步必须 dispatch: [role] via <path>..."}` | developer | `auto_dev_guard.py` | S1.1 |
| S1.5 | `hooks.claude.json` 添加 `PostToolUse` hook section,matcher 空(全量触发),command 同 `auto_dev_guard.py posttooluse` | developer | `hooks.claude.json` | S1.3 |
| S1.6 | SKILL_CORE.md §5.2 旧模型名称表清理: sonnet/opus/haiku → minimax/fable; 更新 Codex CLI 调用表为 gpt-5.5 | developer | `SKILL_CORE.md` | — |

### CAT-2: gpt-5.4 → gpt-5.5 全局替换

| Step | 描述 | 角色 | 文件 | 前置 |
|---|---|---|---|---|
| S2.1 | `_codex-runtime.ps1` line 312: `$Model = 'gpt-5.4'` → `'gpt-5.5'`; 所有 gpt-5.4 引用替换 | developer | `_codex-runtime.ps1` | — |
| S2.2 | `run-codex-plan.ps1`: 默认 Model gpt-5.4→gpt-5.5; prompt 文本 "Default assumption: Codex A/B/C use gpt-5.4" → "use gpt-5.5" | developer | `run-codex-plan.ps1` | — |
| S2.3 | `run-codex-review.ps1`: 默认 Model gpt-5.4→gpt-5.5; prompt 文本替换 | developer | `run-codex-review.ps1` | — |
| S2.4 | `run-codex-implement.ps1`: 默认 Model gpt-5.4→gpt-5.5 | developer | `run-codex-implement.ps1` | — |
| S2.5 | `WORKFLOW.md`: 所有 gpt-5.4→gpt-5.5 替换; `CATEGORY_LOOP` 中 "CATEGORY_PLAN_REVIEW ← 审一次:首次交付 gpt-5.4,返工周期 gpt-5.5" → "审一次:统一 gpt-5.5,effort 分层 high(首次)/xhigh(返工)"; 全部 "GPT-5.4"→"GPT-5.5" 并调整周边语义 | developer | `WORKFLOW.md` | — |
| S2.6 | `PLAN_AGENT_SELECTION.md`: JSON 示例 `"first_review_model": "gpt-5.4"` → `"gpt-5.5"`; 删除旧的 sonnet/opus 派单参考 | developer | `PLAN_AGENT_SELECTION.md` | — |
| S2.7 | `MODEL_QUOTA_CHECK.md.template`: 所有 gpt-5.4→gpt-5.5; 派单可用模型列表 developer/tester/researcher 行: sonnet/opus/haiku → minimax; 加注释 "本环境 minimax 为唯一可用 Claude shell 模型; fable→deepseek-v4-pro 为深层推理; sonnet/opus/haiku 不可用" | developer | `MODEL_QUOTA_CHECK.md.template` | — |
| S2.8 | `SKILL_CORE.md` 残留 gpt-5.4 引用 → gpt-5.5(§3 钩子表 line 281 / §5.1 line 348 / §5.2 lines 530-577); 语义更新为 "统一 gpt-5.5 + effort 分层" | developer | `SKILL_CORE.md` | S1.6 |

### CAT-3: auto-code-android-dev SKILL.md

| Step | 描述 | 角色 | 文件 | 前置 |
|---|---|---|---|---|
| S3.1 | 添加 §0.5 "项目侧文档沉淀路径": `docs/<skill>/<YYYY-MM-DD-task>/` 规则 + 示例 | developer | `auto-code-android-dev/SKILL.md` | — |
| S3.2 | 删除 line 107 过期 TODO("实现待办: 给 run-codex-*.ps1 + _codex-runtime.ps1 补 -Effort→codex exec --effort 透传") | developer | `auto-code-android-dev/SKILL.md` | — |

### CAT-4: show_session_context.py

| Step | 描述 | 角色 | 文件 | 前置 |
|---|---|---|---|---|
| S4.1 | `cmd_init` 新增 `--effort` 参数(positional arg 6); registry entry 增加 `effort` 字段; usage 字符串更新 | developer | `show_session_context.py` | — |
| S4.2 | `cmd_print` 输出行追加 `model=<X> effort=<Y>` 字段(在 `scope` 后); 边界: effort 为空时不显示 | developer | `show_session_context.py` | S4.1 |

### CAT-5: 集成验证

| Step | 描述 | 角色 | 文件 | 前置 |
|---|---|---|---|---|
| S5.1 | 全量 grep 扫描: `gpt-5.4` 残留在 `_shared/` + `auto-code-android-dev/` + `auto-dev/` 下所有 .md/.ps1/.py 文件; 确认仅剩历史注释/禁用说明 | tester | — | CAT-1, CAT-2 |
| S5.2 | 全量 grep 扫描: `sonnet`/`opus`/`haiku` 残留在上述目录; 确认仅在"不可用/禁用"上下文中出现 | tester | — | CAT-1, CAT-2 |
| S5.3 | 验证 Gate 6: mock `{"tool_name":"Agent","subagent_type":"auto-dev-developer","model":"sonnet"}` → deny | tester | `auto_dev_guard.py` | S1.1 |
| S5.4 | 验证 Gate 6 允许: mock `{"tool_name":"Agent","subagent_type":"developer","model":"minimax"}` → allow | tester | `auto_dev_guard.py` | S1.1 |
| S5.5 | 验证 Stop hook block: mock Stop with active task context `current_stage=planning` → `"continue":false` | tester | `auto_dev_guard.py` | S1.4 |
| S5.6 | 验证 `install-agents.ps1` 输出: `~/.claude/agents/claude-developer.md` 存在且 `name: developer` | tester | `install-agents.ps1` | — |
| S5.7 | 验证 `show_session_context.py print` 含 model/effort: 先 init 再 print,检查输出行格式 | tester | `show_session_context.py` | S4.2 |
| S5.8 | 验证 `dispatch.ps1` echo: `pwsh -File dispatch.ps1 -Action codex-review -ProjectRoot . -TaskDir .ai/tasks/X -Effort high` stdout 第一行 `[dispatch] 派 [...]` | tester | `dispatch.ps1` | — |

---

## 5. 允许的修改范围(按类别)

### CAT-1

- **允许修改**:
  - `auto_dev_guard.py`: Gate 6 `KNOWN_AUTO_DEV_AGENT_TYPES` 集合 + 错误消息; 新增 Gate 7 logic; 新增 `handle_posttooluse` 函数; 修改 `handle_stop` 返回逻辑; `main()` 注册 `posttooluse` handler
  - `hooks.claude.json`: 新增 `PostToolUse` hook section
  - `SKILL_CORE.md` §5.2: 模型名称表 + Codex 调用表更新

- **禁止**: 修改 `STATE_SCHEMA` / `PIPELINE_STATE_SCHEMA`; 修改 Gate 1/1.5/2/3/4/5 逻辑(除 forward-compat 需要外); 修改 `dispatch.ps1`

### CAT-2

- **允许修改**:
  - Codex runner 脚本: 默认 `$Model` 值; prompt 文本中的模型名
  - `WORKFLOW.md`: gpt-5.4→gpt-5.5 所有出现; 语义文本 "首轮 GPT-5.4"→"统一 gpt-5.5 + effort 分层 high/xhigh"
  - 模板文件: JSON 示例值 + 文本
  - `SKILL_CORE.md`: gpt-5.4 残余引用 + 旧模型名称

- **禁止**: 修改 `_codex-runtime.ps1` 的 `Invoke-CodexObservedRun` 核心逻辑; 修改 `WORKFLOW.md` 的流程结构; 修改 `SKILL_CORE.md` 的核心禁令 / state schema

### CAT-3

- **允许修改**: `auto-code-android-dev/SKILL.md`: 新增 §0.5 section; 删除过期 TODO
- **禁止**: 修改 Android 门禁规则 / pipeline 定义 / Codex runner 调用说明

### CAT-4

- **允许修改**: `show_session_context.py`: `cmd_init` + `cmd_print`; usage 字符串
- **禁止**: 修改 `THRESHOLD_BY_MODEL` 阈值表; 修改 `cmd_record` 逻辑

### CAT-5

- **允许**: 全量 grep + 手工/mock 验证; 写 `TEST_REPORT.md` + `TEST_REPORT.summary.md`
- **禁止**: 在验证阶段修改任何源码

---

## 6. 快速自检 / 形式化测试 / 全量回归覆盖

### 每步必做自检

| 检查项 | 方式 |
|---|---|
| 修改后文件无 Python 语法错误 | `python -m py_compile auto_dev_guard.py` / `show_session_context.py` |
| 修改后 JSON 合法 | `python -c "import json; json.load(open('hooks.claude.json'))"` |
| PowerShell 脚本无语法错误 | `powershell -NoProfile -Command "Get-Command -Syntax <path>"` |
| Markdown 文件无破坏性改变(mandatory section header 仍在) | grep 验证 `^## 0\.` / `^## 5\.` 等 section 存在 |

### 形式化测试(由 tester 在 CAT-5 执行)

| 测试 ID | 输入 | 预期输出 | 覆盖 AC |
|---|---|---|---|
| T1 | `echo '{"tool_name":"Write","file_path":"src/main/Foo.kt"}' \| python auto_dev_guard.py pretooluse <state_dir>` (STATE.json pipeline state=planning) | `{"continue":false,"reason":"...GATE 1..."}` | AC1 |
| T2 | `echo '{"tool_name":"Agent","subagent_type":"auto-dev-developer","model":"sonnet"}' \| python auto_dev_guard.py pretooluse <state_dir>` | `{"continue":false,"reason":"...GATE 6..."}` | AC4 |
| T3 | `echo '{"tool_name":"Agent","subagent_type":"developer","model":"minimax"}' \| python auto_dev_guard.py pretooluse <state_dir>` | `{"continue":true}` | AC4 |
| T4 | `echo '{"tool_name":"Agent","subagent_type":"deepseek-planner","model":"fable"}' \| python auto_dev_guard.py pretooluse <state_dir>` | `{"continue":true}`, stdout/stderr 含 dispatch echo | AC2 |
| T5 | Stop hook with task_context `current_stage=planning` | `{"continue":false,"reason":"...active task 未完成..."}` | AC6 |
| T6 | Stop hook with task_context `current_stage=done` | `{"continue":true}` | AC6 |
| T7 | `python show_session_context.py init <reg> <sid> minimax developer` + `print <reg> <sid>` | 输出含 `model=minimax effort=` | AC9 |
| T8 | `pwsh -File G:\ai-toolkit\skills\auto-dev\scripts\install-agents.ps1` | `~/.claude/agents/claude-developer.md` 存在且 `name: developer` | AC8 |

### 全量回归

- 所有现有 hook (PreToolUse Gate 1-6 + Stop + UserPromptSubmit) 功能无退化: mock 已知合法/非法输入各一次
- `dispatch.ps1` 三种 Action (codex-plan/codex-review/codex-implement) 参数解析无报错: 仅验证参数绑定(实际跑 Codex 由 review 阶段做)
- `SKILL_CORE.md` 所有 mandatory section (0, 0.5, 0.6, 0.6.4, 0.7, 1-11) 结构完整

---

## 7. 高风险验证检查点(不能等到最后)

| 检查点 | 时机 | 方式 | 失败处理 |
|---|---|---|---|
| CP1: Gate 6 白名单不破坏现有 auto-dev-developer 等旧类型 | S1.1 完成后立刻 | mock 旧 `subagent_type` + valid model → 确认 allow | 回滚 S1.1,仅追加新类型不改旧 |
| CP2: Gate 7 dispatch echo 不破坏现有 PreToolUse JSON 输出格式 | S1.2 完成后立刻 | 检查 stdout 最后一行为合法 JSON `{"continue":true/false}` | dispatch echo 写到 stderr 而非 stdout |
| CP3: handle_posttooluse 不阻塞非 Agent tool 的 PostToolUse 事件 | S1.3 完成后立刻 | mock `{"tool_name":"Read","tool_response":"..."}` → allow | 加 tool_name 过滤 |
| CP4: handle_stop block 不阻止正常 session 结束(如用户 Ctrl+C) | S1.4 完成后立刻 | 检查 hook_input 的 `stop_reason` 字段逻辑 | 仅为 auto-dev active 时 block; `stop_reason=interrupt` 放行 |
| CP5: WORKFLOW.md gpt-5.4 替换不破坏语义: 确认"返工升级"概念转为 "effort xhigh" 而非直接删除 | S2.5 完成后立刻 | 人工阅读修改后段落 | 逐句 check |
| CP6: SKILL_CORE.md 修改不引入自相矛盾(如 §0.5 说只有 minimax/fable 可用,但 §5.2 仍提 sonnet) | S1.6+S2.8 完成后立刻 | 全文件 grep sonnet/opus/haiku | 清理所有不一致 |

---

## 8. 风险 / 回滚 / 非目标

### 风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| Gate 6 白名单变更后旧 dispatch(如 auto-dev-developer)不再被识别,导致现有流程中断 | 中 | CP1: 保留旧类型兼容,仅加新类型 + 模型校验 |
| handle_posttooluse 在 Claude Code hook 环境可能不被触发(Claude Code PostToolUse 支持度未完全验证) | 中 | 先加 hook 注册,若实测不触发则降级为 PreToolUse 的 agent audit + Stop hook enforce |
| handle_stop block 可能导致用户无法正常退出 Claude Code 会话 | 高 | CP4: 仅 block auto-dev active 时的 end_turn; 用户 Ctrl+C / exit 命令放行 |
| WORKFLOW.md 语义变更可能导致 reviewer 在返工时不升级 effort | 中 | CP5: 人工逐句审核,保留"返工 = 升级"语义但改为 effort xhigh |
| grep 全量替换 gpt-5.4 可能误伤历史记录/示例/注释中的合理引用 | 低 | 审每个替换前后 2 行上下文 |
| install-agents.ps1 当前只复制 `deepseek-*.md`(line 57 注释),需验证是否也复制 developer/tester/researcher | 低 | install-agents.ps1 用 `Get-ChildItem -Filter '*.md'` 全量复制,已覆盖 |

### 回滚

- 所有改动通过 Git commit 原子提交: `git revert <commit>` 即可回滚
- CAT-1/2/3/4 各自独立 commit,便于单类回滚
- SKILL_CORE.md / WORKFLOW.md 改动前后保留 diff.patch

### 非目标(Not in scope)

- 不修改 `STATE.json` schema 或 pipeline 状态机
- 不新增 Skill 或 plugin
- 不修改 `install-all.ps1`(主编排已动过且合并冲突待处理)
- 不修改 `_shared/MODEL_ROUTING.md`(若有 gpt-5.4 残余,报给 plan review 但不在此 PLAN 范围)
- 不实际跑 Codex CLI(由 review 阶段的 `[reviewer:codex]` 负责)
- 不修改 `.reasonix/` 或 `vendor/` 下的文件
- 不在 `G:\IronWIl0329\IronWill\` 项目侧做任何改动

---

## 9. 需要用户澄清的未知项

| # | 问题 | 默认假设 | 影响 |
|---|---|---|---|
| U1 | auto_dev_guard.py `handle_posttooluse` 的 `AGENT_SESSION:` 行格式是否已稳定?目前 dispatch.ps1 不产出此格式,claude-developer.md 的 REPORT_FORMATS 规定 `AGENT_SESSION: <sid>` | 格式为 `AGENT_SESSION: <sid>` (一行),用 regex `^AGENT_SESSION:\s*(\S+)` 解析 | S1.3 实现方式 |
| U2 | Claude Code PostToolUse hook 在当前版本 (v2.1.185) 是否支持?若 hooks.claude.json 注册了但不触发怎么办? | 默认支持;若不触发则降级到 PreToolUse audit + Stop block 双重 enforce | S1.5 + 验收方式 |
| U3 | `AGENT_REGISTRY.json` 的 schema 是否需要新增 `dispatches[]` 字段?当前 registry 只定义 `sessions` | 新增 top-level `dispatches` 数组,每项含 `{timestamp, role, model, effort, task, session_id, sub_session_id}` | S1.2 实现 |
| U4 | WORKFLOW.md 中 "CATEGORY_PLAN_REVIEW ← 审一次:首次交付 gpt-5.4,返工周期 gpt-5.5" 改为 "统一 gpt-5.5" 后,是否保留 "首次 vs 返工" 的区分语义? | 保留区分但改为 effort 分层: 首次 `high`, 返工 `xhigh` | S2.5 语义 |
| U5 | MODEL_QUOTA_CHECK.md.template 中 `sonnet`/`opus`/`haiku` 替换为 `minimax` 后,是否需要保留旧模型名作为"不可用"注释? | 是,加注释 "本环境不可用: sonnet/opus/haiku; 可用: minimax(默认), fable→deepseek-v4-pro(深层推理)" | S2.7 内容 |
| U6 | install-agents.ps1 的 line 57 注释说 `Verify with: Get-ChildItem $destDir\deepseek-*.md`,但实际安装的是 developer/tester/researcher(非 deepseek-*),是否需更新? | 更新注释为 `Get-ChildItem $destDir\claude-*.md` | 文档小修,不阻塞 |

---

## PLAN_REVIEW_REQUEST

> 此 PLAN 需由 `[reviewer:codex]` 审查后才能进入 TEST_TARGET。
>
> **审查命令**:
> ```powershell
> pwsh -File G:\ai-toolkit\skills\_shared\scripts\dispatch.ps1 `
>   -Action codex-review `
>   -ProjectRoot G:\ai-toolkit `
>   -TaskDir G:\ai-toolkit\docs\auto-dev\2026-07-09-skill-meta-tdd-flow `
>   -Effort high `
>   -ReviewScope category
> ```
>
> **审查范围**: 需求覆盖完整性、文件范围准确性、Gate guard 逻辑正确性、验收标准可验证性、风险与回滚充分性。
>
> **预期产出**: `G:\ai-toolkit\docs\auto-dev\2026-07-09-skill-meta-tdd-flow\PLAN_REVIEW.current.md`
