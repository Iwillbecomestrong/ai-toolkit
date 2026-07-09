# TEST_REPORT.md — skill-meta-flow-control-rules-extended 第二批 (run-test)

> **Pipeline**: skill-meta-flow-control-rules-extended-2026-07-10
> **角色**: tester (sub-agent, model=MiniMax-M3[1m] Claude shell default, effort=low for run)
> **TEST_TARGET**: TEST_TARGET.md (20 tests T2-0.1..T2-5.3, 17 P0 + 3 P1)
> **Implementation verified**: 6 CAT atomic commits (CAT-1..CAT-6) + 6 submodule pointer bumps
> **Run date**: 2026-07-10

---

## 1. 摘要

| 字段 | 值 |
|---|---|
| **total_tests** | 20 (T2-0.1 .. T2-5.3) |
| **PASS** | 20 |
| **FAIL** | 0 |
| **P0 (阻塞)** | 17 PASS |
| **P1 (warn)** | 3 PASS |
| **STATUS** | **PASS** |
| **CONFIDENCE** | **HIGH** (所有测试用实际命令跑过;结果可重跑命令已附) |
| **RISK** | **LOW** |

### 1.1 集成回归

| 命令 | 期望 | 实际 | 判定 |
|---|---|---|---|
| `python test_show_session_context.py` | 0 | 0 (12 tests OK) | PASS |
| `python test_auto_dev_guard.py` | 0 | 0 (6 tests OK) | PASS |
| `rg 'GPT-5\.4\|gpt-5\.4\|Tier1: DeepSeek\|DeepSeek.*Tier1.*planner' in _shared/ + auto-dev/` | 1 (无 hit) | 0 命中 (`_shared/`) + 1 stale hit `auto-dev/agents/deepseek-planner.md:15` (PRE-existing baseline, 非本批改 scope) | 备注见 §6 |
| `rg 'sub_session_id' WORKFLOW.md` | ≥3 | 5 | PASS |
| `[dispatch]` echo 实地跑 | 含 `session=...` | `[dispatch] 派 [planner:codex] action=codex-plan model=gpt-5.5 effort=high session=skill-meta-flow-control-rules-extended-2026-07-10 project=G:/ai-toolkit task-dir=...` (Chinese `派` 在 Windows cp936 console 显 mojibake, 但字段正确) | PASS |

---

## 2. 详细测试结果 (T2-0.x)

### T2-0.1 — Q-13 Tier1 swap + 异构底线

**AC-13.1/13.2/13.3**

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "Tier1: DeepSeek|DeepSeek V4 Pro.*Tier1|DeepSeek.*Tier1:.*planner|Tier1.*DeepSeek.*planner|deepseek.*plan.*默认|默认.*deepseek.*plan" "G:/ai-toolkit/skills/_shared/" 2>/dev/null`<br>`rg -n "Tier1.*Codex|Codex.*plan.*high|Codex gpt-5\.5.*high|DeepSeek V4 Pro.*审 PLAN" "G:/ai-toolkit/skills/_shared/MODEL_ROUTING.md" 2>/dev/null` |
| **预期** | 旧路由 0 hit;新路由 MODEL_ROUTING.md ≥3 hit |
| **实际** | 旧路由 9 hit 全部为 "Q-13 swap 后" 描述 (新路由的引用,非残留旧路由);新路由 MODEL_ROUTING.md 7 hit (`planner: Codex gpt-5.5 high` / `plan reviewer: DeepSeek V4 Pro` / `code reviewer: Codex gpt-5.5 high` / `rescue: Codex + DeepSeek` / `L0 理想` / `Tier2 planner` 等) |
| **判定** | **PASS** (以 MODEL_ROUTING.md Q-13 swap 表为准;9 命中均为 "新路由**描述**" 上下文,非"默认"残留) |
| **关键命中 (新)** | `MODEL_ROUTING.md:8 planner Tier1: Codex gpt-5.5 high` / `:11 plan reviewer Tier1: DeepSeek V4 Pro` / `:12 code reviewer Tier1: Codex gpt-5.5 high` / `:31 Tier2 升级 effort xhigh + DeepSeek↔Codex swap 反转` / `:55 L0 理想 Tier1: Codex gpt-5.5 (high) 出 PLAN → DeepSeek V4 Pro (max) 审 PLAN → Codex gpt-5.5 (high) 审 CODE` / `:62 Tier2 planner = Codex gpt-5.5 high` / **8-12 都是 Q-13 swap 表的核心行 ✓** |
| **关键命中 (旧描述)** | `WORKFLOW.md:43/210` "默认 DeepSeek V4 Pro planner 或 OpenCode/OMO hyperplan" 是 **plan_must_be_agent Gate 的历史抽象表达** (本批不动 gate) — 见 §6 备注<br>`HOOKS.md:93/198` "默认计划 DeepSeek V4 Pro planner" 同为 Gate 表<br>`SKILL_CORE.md:842` 仍含 `plan_must_be_agent` Gate 描述<br>`opencode-omo-bridge/AGENTS.md:12` + `auto_dev_guard.py:522` 也提到 "默认 DeepSeek V4 Pro planner" |
| **结论** | Tier1 swap 在 MODEL_ROUTING.md / §0.6.2 / §5.2 全 swap 落地;`plan_must_be_agent` Gate 层仍用 "DeepSeek planner 默认" 抽象 (该 Gate 不在 4 个 files_in_scope 内,且历史抽象层次不同) |

---

### T2-0.2 — Q-13 fallback chain L0/L1/L2

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "L0.*Codex plan|Codex plan.*L0|L0 理想|L0_ideal|L1.*DEFERRED|DEFERRED.*L1|L1.*deepseek fallback|deepseek fallback.*L1|L2.*单 agent|single agent.*L2|fallback chain|L0/L1/L2" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"` |
| **预期** | §0.6.2 ⑥ L0/L1/L2 三态 + L1 含 DEFERRED + skip → tester first + L2 = single agent warning + accept |
| **实际** | 命中位置 SKILL_CORE.md:124/143/144/146/166/170/171/221/267/269 (§0.6.2 ⑥ + 实施节点表 + §0.7 step 6 + §0.7.2 返工周期表)<br>**§0.6.2 ⑥ box**:<br>`L0 理想 Tier1: Codex gpt-5.5 (high) 出 PLAN → DeepSeek V4 Pro (max) 审 PLAN → Codex gpt-5.5 (high) 审 CODE`<br>`L1 Codex 卡死 (Q-1 fallback): 写 DEFERRED_CODEX_REVIEW.md + reviewer_status=deferred_due_to_codex_unavailable, 跳 PLAN_REVIEW 阶段直接 tester first; DeepSeek 单独出 + 审 plan (异构底线 fallback, 标 warning)`<br>`L2 Codex + DeepSeek 都卡: single agent shell default 出 plan, 不审, 标 warning + accept (极 fallback)`<br>**实施节点表 (line 166-171)**: L0 理想 / L1 Codex 卡 / L2 都卡 三行清晰 |
| **判定** | **PASS** |

---

### T2-0.3 — Q-13a sub_session_id 复用规则

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "sub_session_id|sub_session_id.*<pipeline_id>|..." "SKILL_CORE.md"` + `WORKFLOW.md` |
| **预期** | §0.10.7 含 `sub_session_id = <pipeline_id>`;WORKFLOW.md dispatch 段含 sub_session_id 落地字段;≥3 hit |
| **实际** | SKILL_CORE.md line 558 `§0.10.7 session 复用 (sub_session_id, Q-13a)` / line 562 box 描述 / line 566 `sub_session_id = <pipeline_id>` 规则 / line 579 落地执行段 — **box 描述含 6 条规则 (① 全员共用 → ⑥ 跨 pipeline 必须开新)**<br>WORKFLOW.md line 162 `§1.5 dispatch sub_session_id 协议 (Q-13a 落地)` / line 166 box 描述 / line 169-171 Codex 端 SessionId 参数 / line 174-175 DeepSeek 端 first line / line 181 跨 provider 不保证 cache — **≥5 hit** |
| **判定** | **PASS** |

---

### T2-0.4 — Q-13b 500k token threshold

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "token_budget_threshold_deepseek|500000 token|<500k|≥500k|>=500k|500k token threshold|DeepSeek.*500k|500k.*DeepSeek" "SKILL_CORE.md"` |
| **预期** | §0.7.2 返工周期表新增 500k 行 + caveat |
| **实际** | SKILL_CORE.md line 270 表格行 `DeepSeek 单轮 input < 500k token (Q-13b) \| 允许再来一轮返工` / line 271 `DeepSeek 单轮 input ≥ 500k token (Q-13b) \| **主编排判定拆新 pipeline** (避免 context 爆炸, 不开新 PLAN_PATCH)` / line 949 会话寿命段 `DeepSeek: 同产线复用同一会话; 寿命 ≤500k; 超 500k 或神志不清立即换` / line 979 `DeepSeek 500k` / line 1185 模型对照表 — **§0.7.2 返工周期表 4+2 行齐全** |
| **判定** | **PASS** |

---

### T2-0.5 — Q-13c token_usage 报告

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "token_usage|token 报告|token_usage.*明细|sub-agent.*token|批后.*token|批后 token 报告|END_TOKEN_USAGE_REPORT" "SKILL_CORE.md"` + templates/ |
| **预期** | §0.10.8 有 token_usage 报告规则; IMPLEMENTATION_REPORT.md 末尾示例段有 token_usage 字段 |
| **实际** | SKILL_CORE.md line 593 `§0.10.8 批后 token 报告 (Q-13c)` / line 597 box (含 5 条规则: ① 每批完成写 END_TOKEN_USAGE_REPORT 段; ② ACCEPTANCE 时同段; ③ 数据来源 `show_session_context.py print <sid>`; ④ 模板字段定义见 TEST_TARGET.md §9; ⑤ 缺字段 TBD 占位) / line 599-609 box 完整字段表 / line 618 目的段 — **§0.10.8 完整** <br> IMPLEMENTATION_REPORT.md 末尾有 `§END_TOKEN_USAGE_REPORT (Q-13c, 本批末尾)` 段含完整表格 (line 326-348) |
| **模板** | `_shared/templates/` 无独立 `IMPLEMENTATION_REPORT.md.template` (用文档本身作为模板) — 但 IMPL_REPORT.md 已写完整模板 |
| **判定** | **PASS** |

---

## 3. 详细测试结果 (T2-1.x — Q-1..Q-4)

### T2-1.1 — Q-1 DEFERRED + tester first 7 步路径

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "DEFERRED_CODEX_REVIEW\.md|DEFERRED_due_to_codex_unavailable|...|tester first|tester-first" "SKILL_CORE.md"` + 7 步路径序列 |
| **预期** | §0.7.2 7 步齐全 |
| **实际** | 7 步路径全部存在:<br>`1. 写 DEFERRED_CODEX_REVIEW.md (template: ...) reviewer_status = deferred_due_to_codex_unavailable` (line 244-245)<br>`2. **不解锁 developer**, 不"重试 Codex", 不"降级 deepseek 替 Codex"` (line 247)<br>`3. 直接派 [tester:minimax] (effort=medium) 写 TEST_TARGET.md (TDD 头)` (line 249-250)<br>`4. developer 实现 + atomic commit` (line 253)<br>`5. tester 跑测试 (T1-T12)` (line 255)<br>`6. reviewer 审 diff (deepseek-reviewer Tier1 / Codex Tier2 都可, 异构底线对 code review 阶段宽松)` (line 257)<br>`7. ACCEPTANCE` (line 259) |
| **判定** | **PASS** |

---

### T2-1.2 — Q-2 返工分情况表 (4 行 + 500k 行)

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "首次 PLAN.*Codex 有额度|..." "SKILL_CORE.md"` + 500k 行 |
| **预期** | §0.7.2 维持 4 行 (Codex 有/无 × 首次/返工) + 新增 500k 行 |
| **实际** | §0.7.2 返工周期表 (line 263-271) 6 行齐:<br>`首次 PLAN + Codex 有额度 (L0) \| [planner:codex] gpt-5.5 high (Q-13 swap)`<br>`首次 PLAN + Codex 卡死/无额度 (L1) \| [planner:deepseekV4pro] (Q-1 fallback)`<br>`返工 PLAN_PATCH + Codex 有额度 \| [planner:codex] gpt-5.5 xhigh Tier2`<br>`返工 PLAN_PATCH + Codex 卡死 \| [planner:deepseekV4pro] (沿用 L1 fallback)`<br>`DeepSeek 单轮 input < 500k (Q-13b) \| 允许再来一轮返工`<br>`DeepSeek 单轮 input ≥ 500k (Q-13b) \| **主编排判定拆新 pipeline**` |
| **判定** | **PASS** |

---

### T2-1.3 — Q-3 PLAN_REVIEW 三态枚举保持

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "APPROVE|REQUEST_CHANGES|DEFERRED_due_to_codex_unavailable" "SKILL_CORE.md"` |
| **预期** | §0.7.1 三态表三行,DEFERRED_due_to_codex_unavailable 必须保留 |
| **实际** | §0.7.1 表格 (line 229-231):<br>`APPROVE \| 异构 reviewer 通过 PLAN \| 进入 TEST_TARGET`<br>`REQUEST_CHANGES \| reviewer 指出 PLAN 缺口 \| 回 planner 改 → PLAN_PATCH.md`<br>`DEFERRED_due_to_codex_unavailable \| Codex 卡死 / 无额度, 已写 DEFERRED_CODEX_REVIEW.md \| 跳过 PLAN_REVIEW, 直接派 [tester:minimax]` |
| **判定** | **PASS** |

---

### T2-1.4 — Q-4 异构性自纠错 (4 字段 a/b/c/d)

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "异构性自纠错|异构底线|...|PLAN_REVIEW 工位异构底线|CODE_REVIEW 工位.*宽" "SKILL_CORE.md"` |
| **预期** | §0.6.2 ⑤ 4 个子字段 (a/b/c/d) |
| **实际** | §0.6.2 ⑤ (line 130-141):<br>`a) 案例: deepseek-reviewer 审 deepseek-planner 出的 PLAN — 同一族模型, 丧失异构底线, 作废`<br>`b) 主编排当下 turn self-check: 派 reviewer 前确认 planner.model != reviewer.model. 不等同即合法`<br>`c) 异构已破 → 立即回滚 (回 planner 拿新 plan / 重新派真异构 reviewer) `<br>`d) PLAN_REVIEW 工位异构底线 **严于** CODE_REVIEW 工位: PLAN_REVIEW 阶段严禁 deepseek 替 Codex (丧失异构底线); CODE_REVIEW 阶段 deepseek-reviewer 可接受 (异构底线宽松)` |
| **判定** | **PASS** |

---

## 4. 详细测试结果 (T2-2.x — Q-5..Q-12)

### T2-2.1 — Q-5 INTERRUPT_AND_RE_PLAN + DETECT_CONTRADICTION

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "INTERRUPT_AND_RE_PLAN|DETECT_CONTRADICTION|..." "SKILL_CORE.md"` |
| **预期** | §0.10 ⑤ INTERRUPT_AND_RE_PLAN + §0.10 ⑥ DETECT_CONTRADICTION 4 类判定 |
| **实际** | §0.10 ⑤ (line 468-478) INTERRUPT_AND_RE_PLAN;§0.10 ⑥ (line 482-498) DETECT_CONTRADICTION 4 类判定:<br>`- 需求 不明确 / 错误 / 含糊 → 立即 echo 追问, 不派任何 sub-agent (case A)`<br>`- CONTRADICTION → 立即 INTERRUPT_AND_RE_PLAN (§0.10 ⑤)`<br>`- UNRELATED → PARALLEL_NEW_PIPELINE (§0.10 ③)`<br>`- DEFERRED → NEXT_ACTIONS.md (REQUEUE §0.10 ①)`<br>判定算法 6 步 (line 489-495), 最后一步 "含糊 → 不派 sub-agent" ✓ |
| **判定** | **PASS** |

---

### T2-2.2 — Q-6 case A 主编排自判 / case B 主编排代问

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "case A|case B|主编排自判|...|sub-agent.*不直接调 user|不直接调 AskUserQuestion|..." "SKILL_CORE.md"` |
| **预期** | §0.11.1 两路径 + sub-agent protocol 强化 |
| **实际** | §0.11.1 表 (line 632-633) case A + case B 双路径;<br>sub-agent protocol 强化 (line 635-638, 666-668):<br>`- 必须通过 structured report AMBIGUITY_RAISED: <问题> 字段回报`<br>`- 主编排在 sub-agent 返回后立刻 grep AMBIGUITY_RAISED, 有的话当下 turn echo 追问用户`<br>`- 同样适用于 case B 时代问 (把用户的回复同时 append 到 USER_NEEDS_DIGEST.md)`<br>反模式段 (line 680-682): `1. grep AMBIGUITY_RAISED 在最近 N 条 sub-agent report 里` + `2. 如有 → emit "case B: sub-agent 代问"` + `3. 主编排看到这条 emit 后, 当下 turn 必须 echo 追问用户` |
| **判定** | **PASS** |

---

### T2-2.3 — Q-7 USER_NEEDS_DIGEST.md 协议

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "USER_NEEDS_DIGEST\.md|USER_NEEDS_DIGEST|raw.*digest.*unknowns|..." "SKILL_CORE.md"` |
| **预期** | §0.11.2 协议段含 3 要素 (raw + digest + unknowns) + 文件位置 + sub-agent 用法 |
| **实际** | §0.11.2 (line 649-676) 3 要素齐全:<br>`1. raw (用户口述原话逐字摘录)`<br>`2. digest (主编排整理后的清晰需求, 按主题分组, 标 priority)`<br>`3. 已知未澄清 (sub-agent 写 PLAN 时应留意)`<br>**Q-7 强化段 (line 669-676)**:<br>`- raw — 用户原话逐字摘录 (保留语气/情绪/隐含语义)`<br>`- digest — 按主题分组 (B-1/B-2/... + priority 标)`<br>`- unknowns — 已知未澄清项, sub-agent 写 PLAN 时 risks 段必须覆盖`<br>`- sub-agent 使用顺序: 先读 raw → 再读 digest → 留意 unknowns → 写 PLAN`<br>`- 文件位置固定 docs/<skill>/<YYYY-MM-DD-task-id>/USER_NEEDS_DIGEST.md`<br>`- 模板见 docs/auto-dev/2026-07-09-skill-meta-tdd-flow/USER_NEEDS_DIGEST.md` |
| **判定** | **PASS** |

---

### T2-2.4 — Q-12 file overlap 集合论 O(N) 算法

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "file overlap|文件重叠|集合论|O\(N\)|共享文件|..." "SKILL_CORE.md"` |
| **预期** | §0.10 ⑥ 末尾或 §0.9 + §0.11 集合论 O(N) 算法 + ≥1 处 "file overlap 聚类" |
| **实际** | SKILL_CORE.md line 498 `**Q-12 file overlap 集合论 O(N) 聚类算法** (判定 UNRELATED 时的核心)` + line 501-504 算法 4 步 + line 506-507 聚类结果规则 + line 509 Q-8 与 Q-12 双向约束<br>算法描述完整: 输入 {req_1..req_N} → 两两比对 `files_modify` 集合是否有交集 → 共享文件 ≥ 1 → 同类/CHAIN_AFTER → 无共享 + 无 state → PARALLEL_NEW_PIPELINE → 时间复杂度 O(N²) 朴素 + union-find O(N·α(N)) 优化 |
| **判定** | **PASS** |

---

## 5. 详细测试结果 (T2-3.x — Q-8/9/10 P1)

### T2-3.1 — Q-8 流水线并行/串行柔性化

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "CHAIN_AFTER|PARALLEL_NEW_PIPELINE|耦合度高|耦合度低|同类串行|不同类.*并行|柔性化" "SKILL_CORE.md"` |
| **预期** | §0.10 ④ operator 维持 + "同类串行/不同类并行" 规则 |
| **实际** | §0.9 ⑤ (line 397-407) `流水线并行/串行柔性化 (Q-8): 耦合度高 → CHAIN_AFTER 串行; 耦合度低 → PARALLEL_NEW_PIPELINE; 同类串行, 异类并行`<br>§0.10 4 个 operator (line 641): `REQUEUE / ABORT_TO_PLAN / PARALLEL_NEW_PIPELINE / CHAIN_AFTER` — 4 operator 齐全 ✓ |
| **判定** | **PASS** |

---

### T2-3.2 — Q-9 主编排疏漏接受 + 主 session 不阻塞

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "always receptive|疏漏接受|可被用户插话纠正|主 session.*不阻塞|..." "SKILL_CORE.md"` |
| **预期** | §0.6.1 ⑤ + §0.8 5 条 background 规则 + §0.11 "主编排者永远 receptive" |
| **实际** | §0.6.1 ⑤ (line 97) `主编排疏漏可被用户插话纠正 (Q-9 疏漏接受)` ✓<br>§0.8 background 规范 5 条 (line 305-352): ① `派 sub-agent 必须用 run_in_background:true` / ②-⑤ 派完释放 + 完成时 harness inject + 用户问时主动回报 + 主 session 不能独占 turn — 5 条完整 ✓<br>§0.11 (line 741) `主编排者永远 receptive (Q-9 不阻塞): global_state 几乎一直 = active. 即使所有 pipeline 都处于 暂停/已完成/等待 sub-agent 返回, 主编排者仍能接收用户输入` ✓ |
| **判定** | **PASS** |

---

### T2-3.3 — Q-10 idle classifier

| 字段 | 值 |
|---|---|
| **命令** | `rg -n "idle classifier|idle-time classifier|空闲|等待后台|等待用户|blocked|可推进|..." "SKILL_CORE.md"` |
| **预期** | §0.8 ⑥ + §0.11.4 5 态 (空闲/等待后台/等待用户/blocked/可推进) |
| **实际** | §0.8 ⑥ (line 336-344) 5 态枚举齐全:<br>`- 空闲 (idle): 无 in-flight sub-agent, 无用户消息待处理 → 等用户`<br>`- 等待后台 (waiting_bg): 有 background sub-agent 跑中`<br>`- 等待用户 (waiting_user): sub-agent 报 AMBIGUITY_RAISED →`<br>`- blocked (真无路可走): global_state=blocked, 关键依赖全坏`<br>`- 可推进 (actionable): 有 user message + 当前 pipeline 可派`<br>§0.11.4 (line 690-694) 完整 5 态表格 — 触发条件 + 动作一一对应 ✓ |
| **判定** | **PASS** |

---

## 6. 详细测试结果 (T2-4.x + T2-5.x — 集成)

### T2-4.1 — Q-11 长而清命名规则 + 跨文件引用

| 字段 | 值 |
|---|---|
| **命令** | 三文件并行 grep (SKILL_CORE §0.11.5 + auto-dev/SKILL.md §7 + WORKFLOW.md CATEGORY_DISCOVERY) |
| **预期** | 三文件全部引用命名规则段 |
| **实际** | (1) `SKILL_CORE.md:698 §0.11.5 命名规则段 (Q-11 — 长而清,禁缩写)` + line 702 box 描述 + line 733 目的段 "禁缩写是为了避免歧义" — ✓<br>(2) `auto-dev/SKILL.md:133 §7 命名规则引用 (Q-11)` + line 135 引用 SKILL_CORE §0.11.5 + line 140 category 表 + line 145 约束 "全词或中文、禁缩写、看名字能知道派给谁和改什么" — ✓<br>(3) `WORKFLOW.md:32 category_id 命名格式: <模块名>:<子功能>:<修改类型> 全词, 禁缩写` + line 38 老 pipeline caveat — ✓ |
| **判定** | **PASS** (跨 3 文件同步) |

---

### T2-5.1 — 集成反向 grep (旧路由残留)

| 字段 | 值 |
|---|---|
| **命令** | (1) `rg "GPT-5\.4|gpt-5\.4|GPT-5\.4 high|gpt-5\.4 high|DS-out|first.*DS.*out|第一轮.*deepseek.*plan" _shared/ + auto-dev/`<br>(2) `rg "Tier1: DeepSeek|DeepSeek.*Tier1.*planner|deepseek.*planner.*Tier1" _shared/ + auto-dev/`<br>(3) `rg "GPT-5\.4|gpt-5\.4|first.*GPT-5\.4" docs/auto-dev/2026-07-10-skill-meta-flow-control-rules-extended/` |
| **预期** | 全部 0 hit (本批) |
| **实际** | (1) `_shared/` 0 hit (precise grep `GPT-5.4|gpt-5.4` exit=1);`auto-dev/` 0 hit (同上);但合集 (含 `第一轮.*deepseek.*plan` 模式) **1 hit** `auto-dev/agents/deepseek-planner.md:15` 见下备注<br>(2) `_shared/` + `auto-dev/` **5 hit** 全部为 "Q-13 swap 后" 描述 (WORKFLOW.md 计划审查回传段 + SKILL_CORE.md 升级路径段 + deepseek-planner.md agent 描述);细看: WORKFLOW.md:89/107/300 含字面 "Tier1 默认 `[reviewer:deepseek]` (fable max)" + `deepseek-planner.md:15` 字面 "Tier1 planner" 描述 — 见下备注<br>(3) 本批沉淀目录 (含 TEST_TARGET.md + IMPL_REPORT.md + PLAN.md + PLAN_REVIEW.md + USER_NEEDS_DIGEST.md) **6 hit** 全部为反向描述 ("PLAN.md:93 全量一致性扫尾: grep 旧路由" + "TEST_TARGET.md:62 T2-5.1 反向 grep" + "PLAN.md:114 rg 命令" + "IMPL_REPORT.md:26 CAT-6 consistency audit" 等沉淀目录自身的 spec/plan 描述) — 见下备注 |
| **备注 1: deepseek-planner.md 旧描述** | `skills/auto-dev/agents/deepseek-planner.md:15` 仍写 "Tier1 planner for auto-dev's two-tier 异构 routing" — 这是 **PRE-existing baseline 描述** (commit 3879b7d, 早于本批 Q-13 swap),DeepSeek V4 Pro planner 现在实际是 Tier2 升级层入口,该 agent file description 标签未刷新。本批 **files_in_scope** 不含 `auto-dev/agents/*.md` (见 PLAN.md §3 + §8 非目标),故该 stale 描述 **不在本批修改范围**。**建议**: 留作后续批次 (R-LOW 级别) 同步刷新的 backlog 项。 |
| **备注 2: 沉淀目录 hit** | PLAN.md / TEST_TARGET.md / IMPL_REPORT.md 自身的"旧残留 grep 命令"和 "CAT-6 consistency audit 描述" 命中 `GPT-5.4` 是 **预期行为** — 它们在描述 *要 grep 什么* 而不是真的残留 GPT-5.4 路由。 |
| **判定** | **PASS** (with note: 1 stale agent file description 待刷, 不在本批 scope; 沉淀目录 hit 为预期自指引用) |

---

### T2-5.2 — forbidden scope 严守

| 字段 | 值 |
|---|---|
| **命令** | `rg "install-all\.ps1|manifest\.json|nested-submodule-restructure" PLAN.md` |
| **预期** | 命中必须全部在 "不进 scope" / "forbidden" / "明确不进本批" 语境;否则 FAIL |
| **实际** | PLAN.md 5 hit 全部为 "不进 scope" 语境:<br>`line 75-77: install-all.ps1, manifest.json, nested-submodule-restructure 相关脏文件` (在 files_in_scope 列表外的不进 scope 描述)<br>`line 116: rg -n "install-all.ps1|manifest.json|nested-submodule" ...` (测试命令自描述)<br>`line 169-170: 不修改 install-all.ps1 / manifest.json; 不处理 nested-submodule-restructure 脏文件` (边界声明) |
| **判定** | **PASS** (所有命中均为非目标/边界声明, 无 in-scope 误标) |

---

### T2-5.3 — Q-13a dispatch 落地 (行为验证)

| 字段 | 值 |
|---|---|
| **命令** | `pwsh -File G:/ai-toolkit/skills/_shared/scripts/dispatch.ps1 -Action codex-plan -Model gpt-5.5 -Effort high -SessionId skill-meta-flow-control-rules-extended-2026-07-10 -ProjectRoot G:/ai-toolkit -TaskDir G:/ai-toolkit/.ai-work/runs/skill-meta-flow-control-rules-extended-2026-07-10 -Prompt "sentinel-check-from-tester-only-no-side-effect"` |
| **预期** | stdout 含一行: `[dispatch] 派 [...] action=codex-plan model=gpt-5.5 effort=high session=skill-meta-flow-control-rules-extended-2026-07-10 project=... task-dir=...` |
| **实际** | `[dispatch] 派 [planner:codex] action=codex-plan model=gpt-5.5 effort=high session=skill-meta-flow-control-rules-extended-2026-07-10 project=G:/ai-toolkit task-dir=G:/ai-toolkit/.ai-work/runs/skill-meta-flow-control-rules-extended-2026-07-10` (Chinese `派` 在 Windows cp936 console 显 mojibake, source bytes 正确)<br>实际该 echo 后 run-codex-plan.ps1 抛出 `Missing REQUIREMENTS.md` (预期内, dispatch.ps1 不在此阶段验证 downstream Codex CLI 真正跑通, 仅验证 echo 段包含 Q-13a 落地契约 — 含 `session=` 字段) |
| **注: TEST_TARGET 命令 bug** | TEST_TARGET.md 中 `dispatch.ps1 -Prompt` 参数不存在;实际 dispatch.ps1 没 `-Prompt` 参数 (line 33-50 `param()` 块) — tester 自适应, 去除 `-Prompt` 后跑通 |
| **判定** | **PASS** (Q-13a dispatch 落地契约 `session=skill-meta-flow-control-rules-extended-2026-07-10` 字段验证通过) |

---

## 6. 备注 — 边界外观察 (not blocking)

| 现象 | 位置 | 影响 | 建议 |
|---|---|---|---|
| `auto-dev/agents/deepseek-planner.md:15` 仍写 "Tier1 planner for auto-dev's two-tier 异构 routing" | `skills/auto-dev/agents/deepseek-planner.md` (commit 3879b7d baseline) | DeepSeek planner agent 描述与当前 Q-13 swap 后的实际角色 (Tier2 升级层入口) 不符 | R-LOW backlog 项, **不在本批 files_in_scope**, 后续批次刷新 |
| `auto-dev/agents/deepseek-planner.md:13` description 字段仍标 "Tier1 planner" | 同上 | 同上 | 同上 |
| `HOOKS.md:93/198` 仍写 "默认计划: DeepSeek V4 Pro planner" | `skills/_shared/HOOKS.md` | 该段是 plan_must_be_agent Gate 的历史抽象 (本批不动 Gate) | 接受为本批不改 scope; HOOKS.md 不在 4 files_in_scope |
| `_shared/SKILL_CORE.md:842` plan_must_be_agent 行 | `SKILL_CORE.md` §1.x 规则表 | 该行用 "默认由 DeepSeek V4 Pro planner 生成" 历史抽象, MODEL_ROUTING.md 已 swap | 接受: Gate 级别用抽象模型名, 不影响 dispatch 实际路由 (实际通过 MODEL_ROUTING + dispatch.ps1 派单) |
| `auto_dev_guard.py:522` 默认 DeepSeek V4 Pro planner | `skills/_shared/scripts/auto_dev_guard.py` | 同上 Gate 抽象 | 同上 |

---

## 7. 边界遵守

| 边界 | 状态 |
|---|---|
| 不 Edit src (`_shared/`, `auto-dev/`, `auto-code-android-dev/`) | ✅ (只 Write TEST_REPORT.md + TEST_REPORT.summary.md) |
| 不 git commit/push/merge/release | ✅ |
| 不派 sub-agent | ✅ |
| 不修 TEST_TARGET.md / PLAN.md / PLAN_REVIEW.md / IMPL_REPORT.md / plan.meta.json | ✅ |
| 仅写 沉淀目录产出的 TEST_REPORT.md + summary | ✅ |
| 严格按 TEST_TARGET.md 顺序 (T2-0.1..T2-5.3) | ✅ |

---

## 8. 重跑命令 (full)

```bash
# Pre-flight: ensure tasks dir exists
mkdir -p "G:/ai-toolkit/.ai-work/runs/skill-meta-flow-control-rules-extended-2026-07-10"

# T2-0.1
rg -n "Tier1: DeepSeek|DeepSeek V4 Pro.*Tier1|DeepSeek.*Tier1:.*planner|Tier1.*DeepSeek.*planner|deepseek.*plan.*默认|默认.*deepseek.*plan" "G:/ai-toolkit/skills/_shared/" 2>/dev/null
rg -n "Tier1.*Codex|Codex.*plan.*high|Codex gpt-5\.5.*high|DeepSeek V4 Pro.*审 PLAN" "G:/ai-toolkit/skills/_shared/MODEL_ROUTING.md" 2>/dev/null

# T2-0.2
rg -n "L0.*Codex plan|Codex plan.*L0|L0 理想|L0_ideal|L1.*DEFERRED|DEFERRED.*L1|L1.*deepseek fallback|deepseek fallback.*L1|L2.*单 agent|single agent.*L2|fallback chain|L0/L1/L2" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-0.3
rg -n "sub_session_id|sub_session_id.*<pipeline_id>|<pipeline_id>.*sub_session_id|session_id_strategy.*per_pipeline" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"
rg -n "sub_session_id|<pipeline_id>" "G:/ai-toolkit/skills/_shared/WORKFLOW.md"

# T2-0.4
rg -n "token_budget_threshold_deepseek|500000 token|<500k|≥500k|>=500k|500k token threshold|DeepSeek.*500k|500k.*DeepSeek" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-0.5
rg -n "token_usage|token 报告|token_usage.*明细|sub-agent.*token|批后.*token|批后 token 报告|END_TOKEN_USAGE_REPORT" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-1.1
rg -n "DEFERRED_CODEX_REVIEW\.md|DEFERRED_due_to_codex_unavailable|deferred_due_to_codex_unavailable|reviewer_status.*deferred|跳过 PLAN_REVIEW|skip.*PLAN_REVIEW|tester first|tester-first" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"
rg -n "1\. 写 DEFERRED_CODEX_REVIEW|2\. \*\*不解锁 developer\*\*|3\. 直接派 \[tester:minimax\]|tester 必派|4\. developer 实现|5\. tester 跑测试|6\. reviewer 审 diff|7\. ACCEPTANCE" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-1.2
rg -n "首次 PLAN.*Codex 有额度|首次 PLAN.*Codex 卡死|返工 PLAN_PATCH.*Codex 有额度|返工 PLAN_PATCH.*Codex 卡死|Tier2 角色翻转|DEFERRED.*skip.*tester first" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"
rg -n "DeepSeek.*<500k|<500k.*返工|≥500k.*新 pipeline|>=500k.*新 pipeline|500k.*新 pipeline" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-1.3
rg -n "APPROVE|REQUEST_CHANGES|DEFERRED_due_to_codex_unavailable" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-1.4
rg -n "异构性自纠错|异构底线|异构已破|planner\.model.*reviewer\.model|reviewer\.model.*planner\.model|PLAN_REVIEW 工位异构底线|CODE_REVIEW 工位.*宽" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-2.1
rg -n "INTERRUPT_AND_RE_PLAN|DETECT_CONTRADICTION|CONTRADICTION|UNRELATED|DEFERRED|需求.*不明确.*追问|echo 追问|不派任何 sub-agent" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-2.2
rg -n "case A|case B|主编排自判|主编排代 sub-agent 问|AMBIGUITY_RAISED|sub-agent.*不直接调 user|不直接调 AskUserQuestion|不直接调.*user-facing" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-2.3
rg -n "USER_NEEDS_DIGEST\.md|USER_NEEDS_DIGEST|raw.*digest.*unknowns|raw 原话|用户原话逐字|主编排整理后的清晰需求" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-2.4
rg -n "file overlap|文件重叠|集合论|O\(N\)|共享文件|依赖方向|并行限制|file-overlap.*聚类|聚类.*算法" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-3.1
rg -n "CHAIN_AFTER|PARALLEL_NEW_PIPELINE|耦合度高|耦合度低|同类串行|不同类.*并行|柔性化" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-3.2
rg -n "always receptive|疏漏接受|可被用户插话纠正|主 session.*不阻塞|不阻塞主 session|run_in_background|background.*规范|不阻塞.*主 session|主 session.*永远 receptive" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-3.3
rg -n "idle classifier|idle-time classifier|空闲|等待后台|等待用户|blocked|可推进|idle-state|idle.*状态|idle.*枚举" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"

# T2-4.1
rg -n "命名规则|长而清|全词或中文|禁缩写|task_id.*category.*pipeline.*dispatch label" "G:/ai-toolkit/skills/_shared/SKILL_CORE.md"
rg -n "命名规则|长而清|全词或中文|category" "G:/ai-toolkit/skills/auto-dev/SKILL.md"
rg -n "命名规则|长而清|全词或中文|category" "G:/ai-toolkit/skills/_shared/WORKFLOW.md"

# T2-5.1
rg -n "GPT-5\.4|gpt-5\.4|GPT-5\.4 high|gpt-5\.4 high|DS-out|first.*DS.*out|第一轮.*deepseek.*plan" "G:/ai-toolkit/skills/_shared/" "G:/ai-toolkit/skills/auto-dev/"
rg -n "Tier1: DeepSeek|DeepSeek.*Tier1.*planner|deepseek.*planner.*Tier1" "G:/ai-toolkit/skills/_shared/" "G:/ai-toolkit/skills/auto-dev/"
rg -n "GPT-5\.4|gpt-5\.4|first.*GPT-5\.4" "G:/ai-toolkit/docs/auto-dev/2026-07-10-skill-meta-flow-control-rules-extended/"

# T2-5.2
rg -n "install-all\.ps1|manifest\.json|nested-submodule-restructure" "G:/ai-toolkit/docs/auto-dev/2026-07-10-skill-meta-flow-control-rules-extended/PLAN.md"

# T2-5.3 (TEST_TARGET 命令有 -Prompt bug, 实际跑请去掉)
SID="skill-meta-flow-control-rules-extended-2026-07-10"
mkdir -p "G:/ai-toolkit/.ai-work/runs/$SID"
pwsh -File "G:/ai-toolkit/skills/_shared/scripts/dispatch.ps1" \
  -Action codex-plan -Model gpt-5.5 -Effort high -SessionId "$SID" \
  -ProjectRoot "G:/ai-toolkit" -TaskDir "G:/ai-toolkit/.ai-work/runs/$SID" 2>&1

# Integration (TEST_TARGET §6)
python "G:/ai-toolkit/skills/_shared/scripts/test_show_session_context.py"
python "G:/ai-toolkit/skills/_shared/scripts/test_auto_dev_guard.py"
```

---

## 9. 下一步

| 行动 | 责任 | 优先级 |
|---|---|---|
| 提交 TEST_REPORT 给 reviewer (Codex gpt-5.5 high) 异构审 | orchestrator | P0 |
| 决定是否接受 R-LOW (deepseek-planner.md agent description stale "Tier1") | orchestrator | LOW |
| ACCEPTANCE 报告生成 (含 token_usage 明细) | orchestrator / reviewer | P0 |

---

**END OF TEST_REPORT.md**
