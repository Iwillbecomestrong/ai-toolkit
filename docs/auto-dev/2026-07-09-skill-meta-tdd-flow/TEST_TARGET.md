# TEST_TARGET.md — skill meta 改造 pipeline 测试靶

> tester 阶段 (TDD step 1) — 写测试靶,给 developer 接力实现后由 run-time tester 跑通并写 `TEST_REPORT.md`

---

## 1. Header

| 字段 | 值 |
|------|----|
| **tester_role** | `tester` (写测试靶阶段,注意:本次以 `general-purpose` 替身运行,因为 `claude-tester.md` frontmatter `model: minimax` 是错 id 触发 `Invalid model`) |
| **based_on** | `PLAN.md` 9-section + AC1..AC12 (见 §3 表) |
| **downstream** | 1) `TEST_TARGET_REPORT.md` (本文件写完 echo 后由 tester step-2 写的 "ALL_TARGETS_DEFINED" 索引), 2) `TEST_REPORT.md` (跑完 T1-T12 后的 PASS/FAIL) |
| **risk_level** | **HIGH** (从 `plan.meta.json` 抄; 涉及 hooks、install script、agent dispatcher、frontmatter — 任一处错都是 skill 系统级故障) |
| **generated_at** | 2026-07-09 |
| **session** | <sid> |
| **subagent_type_actual** | `general-purpose` (替身,因 `model: minimax` 拒绝) |
| **model_intended** | minimax2 / shell-default (待 developer 阶段 B1 fix 后才能正常路由) |

### 1.1 与上下游衔接

```
deepseek-planner → PLAN.md (9-section + AC1..AC12)
                ↓
        [tester:minimax] ← YOU ARE HERE (写 TEST_TARGET.md = 流程产物,不在 skill 系统内)
                ↓
TEST_TARGET.md → TEST_TARGET_REPORT.md (index, also tester)
                ↓
developer:minimax → 改 src + atomic commit
                ↓
tester:minimax (run) → TEST_REPORT.md (PASS/FAIL)
                ↓
deepseek-reviewer → REVIEW_REPORT.md (异构 review)
```

> **NOTE**: TEST_TARGET.md 是流程产物,不放进 skill 系统,不进 `install-all.ps1` staging,不算 skill 输出。

---

## 2. 测什么 — 总览

| Tier | 范围 | 数量 |
|------|------|------|
| **P0** | 阻塞 ACCEPTANCE; 任一 FAIL → reject commit | 6 测试组 (T1, T2, T3, T4, T5-a/b/c, T6, T7) |
| **P1** | 推荐测; FAIL 标 warn,developer 自决要不要修 | 4 测试 (T8, T9, T10, T11) |
| **P2** | nice-to-have; FAIL 仅 log | 2 测试 (T12, T12-bug) |

总计 **12 测试** (T1-T12, 含子案例标 -a/-b/-c/-bug/-sub-bug)。

---

## 3. AC ↔ Test 映射表

| AC (from PLAN.md) | 内容摘要 | 对应 T# | 备注 |
|---|---|---|---|
| **AC1** | Gate 1 阻断源码编辑 (Read/Edit/Write/Grep/Glob on `_shared/`, `auto-dev/`, `auto-code-android-dev/` 之外) | **T1** | mock hook_input stdin |
| **AC2** | Gate 7 dispatch audit + AGENT_REGISTRY.json 落盘 `dispatches[]` | **T4** | mock Agent tool call |
| **AC3** | (internal) hooks 整体拓扑 | **不测** | internal routing,靠 install-all 跑通间接覆盖 |
| **AC4** | Gate 6 模型白名单 `{minimax, fable, codex-cli}` | **T3** | NOTE: `minimax` 是 internal id 字面值,实际"default model" 应允许空 model 通过 |
| **AC5-软** | plan-first 工作流 (Developer 必须先有 plan 才开发) | **不单测** (被 T2/T5-b 间接覆盖) | "软" = 行为约束,不是单点 fail |
| **AC6** | handle_stop block in active task (reviewer 提的高风险点) | **T5** (a/b/c) | phase=done / phase=开发+interrupt / phase=开发+end_turn |
| **AC7-软** | Codex 卡死 → DEFERRED → tester first (返工按情况) | **不单测** | NEXT_ACTIONS Q-1/Q-2 → 应在 SKILL_CORE §0.7 落规则,见 §6 B2/B3 |
| **AC8** | install-all.ps1 + install-agents.ps1 跑通 + 5 agent file 落到 `~/.agents/skills/auto-dev/agents/` | **T6** | 含 T6-sub-bug: frontmatter `model: minimax` 错 id 修复 |
| **AC9** | show_session_context.py print 含 `model=` `effort=` 字段 | **T7** | init+print mock |
| **AC10** | WORKFLOW.md / docs 不能写死 `gpt-5.4` 等过期 model 名 | **T11** | 反向 grep |
| **AC11** | (internal) 跨 agent dispatch 注册表落盘 | **不测** (被 T4 覆盖) | internal |
| **AC12** | (internal) effort 透传到 codex exec | **不测** | 已在 `3879b7d` commit 内,无需重测 |

---

## 4. P0 — 必测 (阻塞 ACCEPTANCE)

### T1 — Gate 1 阻断源码编辑

**AC1**

#### Set-up
- 跑 `pwsh -File G:\ai-toolkit\install-all.ps1 -Framework claude` 安装 hooks 到 `~/.claude/`
- 找到 `auto-dev` skill 下 hooks 脚本 (e.g. `G:\ai-toolkit\skills\auto-dev\scripts\hooks\pre_tool_use.py` 或等价二进制) 的入口名
- 准备 hook_input JSON (走 stdin) — mock "developer 阶段试图 Edit `G:\ai-toolkit\_shared\scripts\foo.py`"

#### Input (stdin JSON)
```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "G:\\ai-toolkit\\_shared\\scripts\\foo.py",
    "old_string": "x",
    "new_string": "y"
  },
  "session_context": {"phase": "开发", "agent_role": "developer"}
}
```

#### Expect
- **decision**: `deny`
- **reason**: 含 `GATE 1 BLOCKED` (字面匹配即可,也允许变体 `gate1` `Gate 1` `block-edit-shared` — 至少 one of)
- **exit_code**: `0` (hook 协议 — 异常用 decision:deny 报,不要非 0 exit)
- **stdout**: 单行 JSON,字段 schema 满足 Claude Code hook protocol (`hookSpecificOutput` 或 `decision` + `reason`)

#### Verify
```bash
echo '{...}' | python "G:/ai-toolkit/skills/auto-dev/scripts/hooks/pre_tool_use.py"
# exit 0, decision=deny, reason~=GATE 1 BLOCKED
```

---

### T2 — Gate 1.5 阻断 state=计划 阶段试图开发 (跳级)

**AC5-软** 间接

#### Input (stdin JSON)
```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {"file_path": "G:\\ai-toolkit\\auto-dev\\scripts\\new.py", "content": "..."},
  "session_context": {"phase": "计划", "agent_role": "developer"}
}
```

#### Expect
- **decision**: `deny`
- **reason**: 含 `GATE 1.5` 或等价短语 (e.g. `phase-must-not-skip` `state-plan-block-dev`)
- 注:plan 阶段允许 Read/Glob/Grep,不允许 Write/Edit/Bash(对 src)

#### 反向 case (sanity)
- `phase=开发` + Edit 同 path → 应 allow (T1 用 phase=开发,Edit `_shared/` 才 deny — 区分 Gate 1 vs 1.5)

---

### T3 — Gate 6 模型白名单

**AC4**

#### Input — case-a (accept)
```json
{"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {"model": "minimax", "prompt": "..."}}
```
#### Expect
- **decision**: `allow`

#### Input — case-b (accept — 空 = default)
```json
{"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {"prompt": "no model"}}
```
#### Expect
- **decision**: `allow` ("use default" 视为合法)

#### Input — case-c (deny — sonnet)
```json
{"tool_input": {"model": "sonnet", ...}}
```
#### Expect
- **decision**: `deny`, reason 含 `Gate 6` + `model-not-in-whitelist` 或等价

#### case-d/e/f
- `model=opus` → deny
- `model=haiku` → deny
- `model=fable` → allow
- `model=codex-cli` → allow

#### NOTE (programmer-side)
> `minimax` 这个标识是 **internal placeholder**,实际值不能用 (见 §6 B1)。T3 用 `minimax` 字面过 whitelist 是 contract test;真生产跑时 model 字段应空 (default)。tester 报告里标 "PASS-as-literal, NOTE: model field empty recommended for prod".

---

### T4 — Gate 7 dispatch audit echo + AGENT_REGISTRY.json 落盘 `dispatches[]`

**AC2**

#### Set-up
- 确保 `~/.agents/skills/auto-dev/state/AGENT_REGISTRY.json` 已 init (or create-empty if missing)
- 备份原文件,跑完恢复

#### Input (stdin JSON — mock Agent tool call)
```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Agent",
  "tool_input": {
    "model": "fable",
    "subagent_type": "deepseek-planner",
    "prompt": "PLAN next iteration",
    "description": "Plan next"
  },
  "session_context": {
    "session_id": "test-t4-<ts>",
    "agent_role": "developer",
    "phase": "开发"
  }
}
```

#### Expect
- **decision**: `allow`
- **stdout**: 含 `[dispatch] 派 [deepseek-planner] @ fable:PLAN next iteration` (允许变体如 `[dispatch]` 前缀 + agent 名 + `@` + model + prompt 摘要)
- **AGENT_REGISTRY.json**:
  - `session_id` 对应 session 的 `dispatches[]` 数组 append 一个新条目
  - 新条目含至少: `ts` (ISO8601) + `agent` (=`deepseek-planner`) + `model` (=`fable`) + `phase` (=`开发`)
  - 文件 schema 是 valid JSON

#### Verify
```bash
# 1. dispatch echo
echo '{...}' | python pre_tool_use.py | grep -E '\[dispatch\] 派 \[deepseek-planner\]'

# 2. AGENT_REGISTRY.json 落盘
python -c "import json; r=json.load(open('C:/Users/23248/.agents/skills/auto-dev/state/AGENT_REGISTRY.json','r',encoding='utf-8')); assert any(d.get('agent')=='deepseek-planner' for d in r.get('sessions',{}).get('test-t4-<ts>',{}).get('dispatches',[]))"
```

---

### T5 — handle_stop block in active task

**AC6** (reviewer 提的高风险点)

#### Set-up
- 找到 stop hook (e.g. `handle_stop.py` 或 `hooks/stop.py`),mock Stop hook input

#### T5-a — phase=done, stop_reason=end_turn → allow
**Input:**
```json
{"hook_event_name": "Stop", "stop_reason": "end_turn", "session_context": {"phase": "done", "agent_role": "developer"}}
```
**Expect:** `decision: allow`, exit 0

#### T5-b — phase=开发 + stop_reason=**interrupt** → **block** (高风险点)
**Input:**
```json
{"hook_event_name": "Stop", "stop_reason": "interrupt", "session_context": {"phase": "开发", "agent_role": "developer"}}
```
**Expect:** `decision: block` (或 `deny`),reason 含 `stop-interrupt-in-active-task` 或等价,exit 0

> **Reviewer 注释**: user interrupt 在 phase=开发 中可能丢上下文 (rollback point 未切完)。plan-first 流程希望 stop=interrupt 时强制 stop-and-summary 流程,而不是直接收尾。

#### T5-c — phase=开发 + stop_reason=end_turn → **block** (因为 active task 没切到 done)
**Input:**
```json
{"hook_event_name": "Stop", "stop_reason": "end_turn", "session_context": {"phase": "开发", "agent_role": "developer"}}
```
**Expect:** `decision: block`,reason 含 `phase-must-be-done-before-stop` 或等价

#### 反向 sanity
- T5-a' phase=done + stop_reason=interrupt → allow (done 不再 active)
- T5-b' phase=计划 + stop_reason=interrupt → allow (计划 阶段停,无 active 写)

---

### T6 — install-all.ps1 + install-agents.ps1 跑通 + agents 落盘 + frontmatter fix

**AC8**

#### Step 1: install-all (framework=claude)
```bash
pwsh -File G:\ai-toolkit\install-all.ps1 -Framework claude
```
**Expect:** exit 0,stdout 含 `installed: claude (skills: ...; plugins: ...)`

#### Step 2: install-agents (auto-dev)
```bash
pwsh -File G:\ai-toolkit\skills\auto-dev\scripts\install-agents.ps1
```
**Expect:** exit 0

#### Step 3: 5 个 agent 文件存在
```bash
ls C:\Users\23248\.agents\skills\auto-dev\agents\
# 期望: deepseek-planner.md  deepseek-reviewer.md  claude-developer.md  claude-tester.md  claude-researcher.md
```
**Expect:** 5 个文件全部存在

#### T6-sub-bug — frontmatter `model: minimax` 修复

**当前状态 (已知 bug):** `claude-developer.md` / `claude-tester.md` / `claude-researcher.md` frontmatter `model: minimax` 是 **错 id**,Claude Code runtime 会拒 (`Invalid model` error)。developer 阶段必须修。

**Verify:**
```bash
python -c "
import re, sys
bad = []
for f in ['claude-developer.md','claude-tester.md','claude-researcher.md']:
    p = f'C:/Users/23248/.agents/skills/auto-dev/agents/{f}'
    txt = open(p,'r',encoding='utf-8').read()
    m = re.search(r'^model:\s*(\S+)\s*$', txt, re.M)
    if m and m.group(1) == 'minimax':
        bad.append(f)
    elif not m:
        pass  # 空 model = use default 也合法
sys.exit(1 if bad else 0)
print('all 3 models OK (empty or valid id, none = minimax placeholder)')
"
```
**Expect:** exit 0,`all 3 models OK`. 若 exit 1 → fail,developer 改 frontmatter `model:` 为空 (omit the line entirely) 或 valid id.

> **可选 valid id** (待 developer 确认): `minimax2` / `sonnet` / `default` — 任意一个能过 runtime 即可。**保守推荐: omit `model:` field 让 runtime 走 default**。

#### T6-extra — install-agents.ps1 修 line 57 注释 (deepseek-*.md → *.md)
见 T9 — 这里 verify 时顺带 grep。

---

### T7 — show_session_context.py print 含 `model=` 与 `effort=` 字段

**AC9**

#### Input (mock session init)
- 创建临时 `~/.agents/skills/auto-dev/state/sessions/test-t7-<ts>.json`,含字段:
  ```json
  {"session_id": "test-t7-<ts>", "agent_role": "developer", "model": "minimax2", "effort": "high", "phase": "开发"}
  ```

#### Run
```bash
# 通过 entrypoint (实际命令以 SKILL.md 为准)
python C:/Users/23248/.agents/skills/auto-dev/scripts/show_session_context.py test-t7-<ts>
```

#### Expect (stdout regex)
- `model=\S+` (非空,非 `missing`)
- `effort=\S+` (非空)
- `phase=开发` 或等价
- exit 0

#### 反向 case
- 缺 `effort` 字段 → 应 fallback `effort=default` 或 `effort=unspecified` (允许)

---

## 5. P1 — 推荐测 (非阻塞,warn 级别)

### T8 — dispatch.ps1 `[dispatch]` echo

- 与 T4 同 target,但走 **PowerShell entrypoint** 而不是 hook stdin
- 输入 source: `dispatch.ps1 -Agent deepseek-planner -Model fable -Prompt "..." -SessionId test-t8-<ts>`
- Expect: stdout 含 `[dispatch] 派 [deepseek-planner] @ fable`,exit 0
- 若 dispatch.ps1 还未单独分离 (可能在 hook 内联),允许用 T4 间接覆盖,标 `skipped-merged-with-T4`

### T9 — install-agents.ps1 line 57 注释修复

**T9-bug:** 当前 line 57 附近注释仍写 `deepseek-*.md` (误导 reader,因脚本实际 install 5 agent 包含 claude-*)

#### Set-up
- 读 `G:\ai-toolkit\skills\auto-dev\scripts\install-agents.ps1`,定位注释

#### Verify
```bash
grep -nE 'deepseek-\*\.md|deepseek-only' "G:/ai-toolkit/skills/auto-dev/scripts/install-agents.ps1" || echo "NO_BAD_COMMENT"
```
**Expect:** `NO_BAD_COMMENT`

> 若 developer 阶段未修 (NEXT_ACTIONS Q-3) → tester 标 **SKIPPED (developer-deferred)**,不 fail。

### T10 — hooks.claude.json matcher 同步

**AC3 (internal)**

#### Verify
- `PostToolUse` matcher 覆盖 `Edit|Write|MultiEdit`
- `PreToolUse` matcher 覆盖 `Edit|Write|MultiEdit`
- `UserPromptSubmit` matcher 覆盖 `*` 或空
- `Stop` matcher 覆盖 `*` 或空

```bash
python -c "
import json
h = json.load(open('C:/Users/23248/.agents/skills/auto-dev/hooks/hooks.claude.json','r',encoding='utf-8'))
matchers = {e.get('matcher'): e.get('hooks') for e in h.get('hooks',[]) for _ in [0]}
print(json.dumps(matchers, ensure_ascii=False, indent=2))
"
```
**Expect:** 所有 4 种 hook event 都有 entry,matcher 同步

### T11 — WORKFLOW.md 反向 grep `gpt-5.4`

**AC10**

```bash
grep -rnE 'gpt-5\.4|gpt-5,4' "G:/ai-toolkit/skills/auto-dev/" || echo "NO_GPT54"
grep -rnE 'gpt-5\.4|gpt-5,4' "G:/ai-toolkit/docs/auto-dev/2026-07-09-skill-meta-tdd-flow/" || echo "NO_GPT54_DOCS"
```
**Expect:** 两个 grep 都 echo `NO_GPT54` (无 hit)

> 若只在 changelog / history 段命中,允许,因为是 historical record。tester 自己判断并标 `PARTIAL`。

---

## 6. P2 — nice-to-have

### T12 — claude-{developer,tester,researcher}.md frontmatter 字段全

**AC12 间接**

#### Verify
每个 .md frontmatter 必须含:
- `name:` (非空)
- `model:` (存在;值可空 = use default — 见 T6-sub-bug)
- `effort:` (low|medium|high|max,任一)
- `tools:` 或 `allowed_tools:` (非空 list)

```bash
python -c "
import re, sys
required = ['name','model','effort','tools']
for f in ['claude-developer.md','claude-tester.md','claude-researcher.md','deepseek-planner.md','deepseek-reviewer.md']:
    p = f'C:/Users/23248/.agents/skills/auto-dev/agents/{f}'
    txt = open(p,'r',encoding='utf-8').read()
    fm = txt.split('---',2)[1] if txt.startswith('---') else txt
    miss = [k for k in required if not re.search(rf'^{k}:', fm, re.M)]
    print(f'{f}: missing={miss}')
"
```

#### T12-bug
同 T6-sub-bug,`model: minimax` 应为空或 valid id。

#### 容忍
- `effort` 不存在 → warn (因 Anthropic API 已 default medium,可能省略)
- `tools` 写 `all` 整串 → OK

---

## 7. 已知 bug 段 (programmer's note,给 developer 接力修)

> 这些不是 test fail point,而是 "developer 阶段顺手做" 的 backlog。

### B1 — frontmatter `model: minimax` 错 id

- **影响**:`claude-developer.md` / `claude-tester.md` / `claude-researcher.md` 三文件 frontmatter `model: minimax`
- **错误**: `minimax` 不是真实 model id,Claude Code runtime 会拒 (`Invalid model`);sub-agent dispatch 也会被 hooks Gate 6 误拦(因为 model identifier 形如 `minimax` 命中 whitelist,但运行时找不到 provider)
- **修法** (developer 自选):
  - 方案 A (推荐): **omit `model:` field entirely** → 走 Claude shell default
  - 方案 B: 改成 valid id (e.g. `default` / `sonnet` / `minimax2`) — 需 developer 确认 litellm / runtime mapping
- **影响 commit 范围**: 3 file + 顺带 T6-sub-bug 验证通过

### B2 — SKILL_CORE §0.7 缺 "Codex 卡死 → DEFERRED → tester first" 显式规则

- **NEXT_ACTIONS Q-1**:
  > "Codex 卡死后,应自动建 `DEFERRED_CODEX_REVIEW.md`,然后 tester first 接力,而不是重试 Codex 或跳 phase"
- **当前**:`SKILL_CORE.md` §0.7 只描述 happy path,卡死分支靠 operator 经验
- **修法**:§0.7 加 3 条 bullet:
  1. Codex hook 连续 2 次 timeout (>10min 无 stdout) → 写 `DEFERRED_CODEX_REVIEW.md` (template 见 `_shared/scripts/templates/`)
  2. DEFERRED 后,active session 立刻切到 `phase=tester-first`
  3. reviewer 仍要跑 (异构)
- **影响 commit 范围**:`SKILL_CORE.md` + 可能加 template

### B3 — SKILL_CORE §0.7 缺 "返工分情况" 规则

- **NEXT_ACTIONS Q-2**:
  > "reviewer FAIL 后,应按 fail-type 分类:contract-fail → developer 直接修;design-fail → 回 planner 改 PLAN.md;meta-fail (pipeline 自身) → 升级 user"
- **当前**:SKILL_CORE §0.7 没说怎么分类,全部丢回 developer,会导致 planner 写错反复擦
- **修法**:§0.7 加 "返工决策表":
  ```
  | Fail type | 信号 | 返工目标 |
  | contract-fail | test FAIL 但符合 PLAN | developer |
  | design-fail | reviewer 指出 PLAN 思路错 | planner |
  | meta-fail | hook/install/pipeline 自身坏 | user (升级) |
  ```
- **影响 commit 范围**:`SKILL_CORE.md`

### B4 — SKILL_CORE §0.10 + §0.11 缺 "插话自动判定 contradiction/unrelated/deferred" 规则

- **NEXT_ACTIONS Q-5**:
  > "用户在 active session 中途插话,应自动判定三类:(a) contradiction (与 PLAN/REVIEW 直接冲突),(b) unrelated (新话题),(c) deferred (先记 inbox 后切回)"
- **当前**:§0.10/§0.11 只说 "user 插话 → phase 切回计划" 一刀切
- **修法**:§0.10 加判定树,§0.11 加 auto-tag (记 `00_inbox/<framework>-<topic>.md`)
- **影响 commit 范围**:`SKILL_CORE.md`

### 其他 backlog (NEXT_ACTIONS Q-3, Q-4, ...)
- Q-3: `install-agents.ps1` line 57 注释 = T9
- Q-4: `WORKFLOW.md` 旧 model 名残留 = T11 间接
- Q-6..Q-N: 见 `NEXT_ACTIONS.md`,本次不展开

---

## 8. test runner 命令 (给 run-time tester 用)

> 执行顺序:`install → install-agents → mocks → 跑 T1-T12 → 写 TEST_REPORT.md`

```bash
# ===== Pre-flight =====
pwsh -File G:\ai-toolkit\install-all.ps1 -Framework claude &&
pwsh -File G:\ai-toolkit\skills\auto-dev\scripts\install-agents.ps1 &&

# ===== Sanity: 5 agents + 3 frontmatter bug =====
ls C:/Users/23248/.agents/skills/auto-dev/agents/ | wc -l   # expect 5
python -c "
import re
bad = []
for f in ['claude-developer.md','claude-tester.md','claude-researcher.md']:
    p = f'C:/Users/23248/.agents/skills/auto-dev/agents/{f}'
    txt = open(p,'r',encoding='utf-8').read()
    if re.search(r'^model:\s*minimax\s*$', txt, re.M):
        bad.append(f)
print('BAD model:minimax:', bad)
" &&

# ===== T1: Gate 1 block =====
echo '{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"G:\\\\ai-toolkit\\\\_shared\\\\scripts\\\\foo.py","old_string":"x","new_string":"y"},"session_context":{"phase":"开发","agent_role":"developer"}}' |
  python G:/ai-toolkit/skills/auto-dev/scripts/hooks/pre_tool_use.py

# ===== T2: Gate 1.5 =====
# (类似,改 phase=计划)

# ===== T3..T7: 同 stdin pattern =====

# ===== T11 reverse-grep =====
grep -rnE 'gpt-5\.4' "G:/ai-toolkit/skills/auto-dev/" "G:/ai-toolkit/docs/auto-dev/2026-07-09-skill-meta-tdd-flow/" || echo "PASS-NO_GPT54"
```

---

## 9. RED 报告 (预填)

| 字段 | 值 |
|------|---|
| **targets_defined** | YES (T1-T12 + sub-cases) |
| **RED_state** | **PENDING** (待 run-time tester 执行) |
| **RED_predicted_fail** | T3 (model id 字面值过 whitelist,bug B1), T6-sub-bug (frontmatter `model: minimax`), T9 (line 57 注释若未修) |
| **RED_predicted_pass** | T1, T2, T4, T5-a (其他 T5 子看 SKILL_CORE 实现), T11 (反向 grep 大概率 pass) |
| **next_step** | developer:minimax 修 B1 (mandatory) + 可选修 B2/B3/B4 + implement hook logic,然后 run-time tester 跑 T1-T12 写 `TEST_REPORT.md` |

### 调用 contract
- 本文件 = `READ` 阶段输入 (给 run-time tester + developer)
- `TEST_TARGET_REPORT.md` = `RED_INDEX` (本次写完后 echo 后由 tester step-2 写)
- `TEST_REPORT.md` = `PASS/FAIL` (跑完后写)

---

## 10. 边界与 don'ts

- **只 Write 本文件** TEST_TARGET.md — 流程产物,不算 skill 系统层输出
- **不要** git add / git commit / Bash 改 src
- **不要** Edit / Write `_shared/`, `auto-dev/`, `auto-code-android-dev/` 下任何文件
- **不要** 派其它 sub-agent
- **不要** Read 无关文件 (uconfine to PLAN.md / DEFERRED_CODEX_REVIEW.md / NEXT_ACTIONS.md / SKILL_CORE.md 存在性确认)

---

## 11. self-check echo (写完时由 tester agent 输出)

```
[tester:minimax] TEST_TARGET done.
paths=G:\ai-toolkit\docs\auto-dev\2026-07-09-skill-meta-tdd-flow\TEST_TARGET.md
AC->T#: 12->7
  AC1=T1, AC2=T4, AC3=不测(internal), AC4=T3,
  AC5=AC5-软 notest (被 T2/T5-b 间接覆盖),
  AC6=T5 (含 T5-b interrupt 路径 — reviewer 高风险点),
  AC7=软 (NEXT_ACTIONS Q-1/Q-2 → B2/B3 backlog),
  AC8=T6 (含 T6-sub-bug frontmatter model=minimax),
  AC9=T7, AC10=T11, AC11=不测(internal, 被 T4 覆盖),
  AC12=不测 (3879b7d 已合)
P0 tests: T1 T2 T3 T4 T5-a T5-b T5-c T6 T7
P1 tests: T8 T9 T10 T11
P2 tests: T12
known_bugs_logged: B1 B2 B3 B4
agent_role_actual: general-purpose (替身,因为 model:minimax 错 id 待修)
```

---

**END OF TEST_TARGET.md**
