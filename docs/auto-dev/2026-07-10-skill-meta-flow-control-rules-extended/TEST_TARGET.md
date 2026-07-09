# TEST_TARGET.md — skill-meta-flow-control-rules-extended 第二批 TDD 测试靶

> 本批覆盖 Q-1 ~ Q-13 + Q-13a/b/c = 17 AC（见 PLAN.md §1 + plan.meta.json acceptance_criteria_count=17）。
> tester-first (Q-1) 路径,tester 先写测试靶 → developer 改 source → tester 跑测试。
> 区分上一批 T1-N.M,本批测试用 **T2-N.M** 编号。

---

## 0. Header

| 字段 | 值 |
|---|---|
| **tester_role** | `[tester:minimax]` (本次以 dispatch 子代理 `subagent_type=tester` 跑;effort=medium 写测试,=low 跑测试) |
| **based_on** | `PLAN.md` 9-section + AC-1~AC-17 (Q-1..Q-13 + Q-13a/b/c);`PLAN_REVIEW.md` DECISION=APPROVE |
| **downstream** | `TEST_TARGET_REPORT.md` (RED 索引,tester step-2 写) → `developer` 改 source → `TEST_REPORT.md` + `TEST_REPORT.summary.md` (跑完 T2 后由 tester 写) → `CODE_REVIEW.md` (reviewer 异构审) → ACCEPTANCE |
| **risk_level** | **HIGH** (从 plan.meta.json `risk_level=HIGH` 抄;涉及 MODEL_ROUTING swap + session 复用 + 500k 阈值 + token 报告,任一处错都是 skill 系统级故障) |
| **generated_at** | 2026-07-10 |
| **sub_session_id** | `skill-meta-flow-control-rules-extended-2026-07-10` (Q-13a 同 pipeline 全员共用) |
| **files_in_scope** | 4 个:`_shared/SKILL_CORE.md` + `_shared/MODEL_ROUTING.md` + `_shared/WORKFLOW.md` + `auto-dev/SKILL.md` |

### 0.1 与上下游衔接

```
[planner:codex (已拒)/deepseekV4pro (已成功)] → PLAN.md + plan.meta.json + PLAN_REVIEW.md
                                              ↓
                              [tester:minimax] ← YOU ARE HERE (写 TEST_TARGET.md)
                                              ↓
                                TEST_TARGET.md (本文件)
                                  ↓ (developer 读完)
                                [developer:minimax] 改 source + atomic commit (per CAT-N)
                                  ↓
                                [tester:minimax] (run) → TEST_REPORT.md + TEST_REPORT.summary.md
                                  ↓
                                [reviewer:codex/deepseek] → CODE_REVIEW.md → ACCEPTANCE
```

> **NOTE**: 本批用 L0 active 跑 (Codex plan 实际成功) + L1 fallback 备用 (deepseek-reviewer 已 silently evaluated 6.5w tokens,主编排代写 APPROVE)。tester 不假设 L1/L2 必走,文档已 two-track 写。

---

## 1. 测试索引（20 个 test）

| T2-N.M | 覆盖 AC | 类型 | 描述 | 优先级 |
|---|---|---|---|---|
| **T2-0.1** | AC-13.1/13.2/13.3 | 静态 grep | Tier1 swap + 异构底线 (旧 "DeepSeek 出 plan" / "Tier1: DeepSeek" 已清) | **P0** |
| **T2-0.2** | AC-fallback | 静态 grep | §0.6.2 fallback chain L0/L1/L2 三态枚举 | **P0** |
| **T2-0.3** | AC-13a | 静态 grep | `sub_session_id` 复用规则在 §0.10.7 + WORKFLOW.md | **P0** |
| **T2-0.4** | AC-13b | 静态 grep | 500k token threshold 在 §0.7.2 返工分情况表 | **P0** |
| **T2-0.5** | AC-13c | 静态 grep | `token_usage` 报告规则在 §0.10.8 + IMPLEMENTATION_REPORT 模板 | **P0** |
| **T2-1.1** | AC-1.1 (Q-1) | 静态 grep | DEFERRED + tester first 7 步路径完整 | **P0** |
| **T2-1.2** | AC-2.1 (Q-2) | 静态 grep | 返工分情况表 4 行 (Codex 有/无 × 首次/返工) + 500k 行 | **P0** |
| **T2-1.3** | AC-3.1 (Q-3) | 静态 grep | PLAN_REVIEW 三态枚举保持 | **P0** |
| **T2-1.4** | AC-4.1 (Q-4) | 静态 grep | §0.6.2 ⑤ 异构性自纠错 4 字段 (a/b/c/d) | **P0** |
| **T2-2.1** | AC-5.x (Q-5) | 静态 grep | §0.10 ⑤⑥ INTERRUPT_AND_RE_PLAN + DETECT_CONTRADICTION | **P0** |
| **T2-2.2** | AC-6.x (Q-6) | 静态 grep | §0.11.1 case A/B + §0.11.3 UserPromptSubmit hook | **P0** |
| **T2-2.3** | AC-7.x (Q-7) | 静态 grep | §0.11.2 USER_NEEDS_DIGEST.md 协议段 | **P0** |
| **T2-2.4** | AC-12.1 (Q-12) | 静态 grep | §0.10 ⑥ file overlap 集合论 O(N) 算法 | **P0** |
| **T2-3.1** | AC-8.x (Q-8) | 静态 grep | §0.9 + §0.10 流水线并行/串行柔性化规则 | **P1** |
| **T2-3.2** | AC-9.x (Q-9) | 静态 grep | §0.6/§0.8/§0.11 疏漏接受 + 主 session 不阻塞 | **P1** |
| **T2-3.3** | AC-10.x (Q-10) | 静态 grep | §0.8 + §0.11 idle classifier 多态枚举 | **P1** |
| **T2-4.1** | AC-11.x (Q-11) | 跨文件 grep | "长而清" + 全词或中文 + 跨文件引用 (SKILL_CORE §0.11 + auto-dev/SKILL.md + WORKFLOW.md) | **P0** |
| **T2-5.1** | 集成 grep | 反向 grep | 全文件无 `GPT-5.4` / `gpt-5.4` / 旧 `Tier1: DeepSeek` / `DeepSeek.*Tier1:.*planner` 残留 | **P0** |
| **T2-5.2** | forbidden scope | 反向 grep | PLAN.md 不引用 `install-all.ps1` / `manifest.json` / `nested-submodule-restructure` 作为修改目标 | **P0** |
| **T2-5.3** | dispatch 落地 | 行为 (shell) | dispatch.ps1 `-SessionId` 参数 + `[dispatch] ... session={id}` echo 实际可见 | **P0** |

**test_count = 20** (4 个 P0 集群覆盖 Q-13 全部 5 AC + Q-1~Q-12 大部分 P0,P1 集群覆盖 Q-8/9/10,N-A 集群覆盖 Q-11 + 集成 / scope / dispatch 落地)

---

## 2. AC ↔ Test 映射表

| AC (from PLAN.md §1) | 内容摘要 | 对应 T# | priority |
|---|---|---|---|
| AC-1.1 | Q-1 Codex 卡死 → DEFERRED + tester first + 跳过 PLAN_REVIEW | T2-1.1 | P0 |
| AC-2.1 | Q-2 返工周期表覆盖 (Codex 有/无 × 首次/返工) + 500k threshold | T2-1.2 | P0 |
| AC-3.1 | Q-3 PLAN_REVIEW 三态枚举 APPROVE/REQUEST_CHANGES/DEFERRED_due_to_codex_unavailable | T2-1.3 | P0 |
| AC-4.1 | Q-4 异构性自纠错 (同源审 → 回滚或 DEFERRED) | T2-1.4 | P0 |
| AC-5.x | Q-5 用户插话 4+2 operator (INTERRUPT_AND_RE_PLAN + DETECT_CONTRADICTION) | T2-2.1 | P0 |
| AC-6.x | Q-6 case A 主编排自判 / case B 主编排代问 | T2-2.2 | P0 |
| AC-7.x | Q-7 USER_NEEDS_DIGEST.md 协议 (raw + digest + unknowns) | T2-2.3 | P0 |
| AC-8.1/8.2/8.3 | Q-8 流水线并行/串行柔性化 (耦合度高=CHAIN_AFTER / 低=PARALLEL) | T2-3.1 | P1 |
| AC-9.1/9.2 | Q-9 主编排疏漏可被用户插话纠正;主 session 不因后台 sub-agent 阻塞 | T2-3.2 | P1 |
| AC-10.1/10.2 | Q-10 idle classifier (空闲/等待后台/等待用户/blocked/可推进) | T2-3.3 | P1 |
| AC-11.1/11.2 | Q-11 命名规则长而清;覆盖 task_id/category/pipeline/dispatch label/沉淀目录 | T2-4.1 | P0 |
| AC-12.1 | Q-12 file overlap 聚类算法 (集合论 O(N)) | T2-2.4 | P0 |
| AC-13.1/13.2/13.3 | Q-13 Tier1 swap (Codex plan + DeepSeek review + Codex code) | T2-0.1 | P0 |
| AC-13a.1 | Q-13a session 复用规则 (sub_session_id=<pipeline_id>) | T2-0.3 + T2-5.3 | P0 |
| AC-13b.1 | Q-13b 500k token threshold | T2-0.4 + T2-1.2 | P0 |
| AC-13c.1/13c.2 | Q-13c token_usage 报告 (IMPLEMENTATION_REPORT 末尾 + ACCEPTANCE) | T2-0.5 | P0 |
| AC-fallback | Q-13 fallback chain L0/L1/L2 | T2-0.2 | P0 |

**AC->Test 覆盖率** : 17/17 (100%) ✓

---

## 3. P0 — 必测 (阻塞 ACCEPTANCE)

### T2-0.1 — Q-13 Tier1 swap + 异构底线

**AC-13.1/13.2/13.3 (Q-13)**

#### Set-up
- baseline 已 commit (上一批 SKILL_CORE §0.6.2 描述 "Tier1 出 PLAN = DeepSeek 出 plan → Codex 审 plan" 还是旧路由)
- 本批 swap: §0.6.2 Tier1 出 PLAN = **Codex gpt-5.5 high**;Tier1 审 PLAN = **DeepSeek V4 Pro (max)**;Tier1 审 CODE = **Codex gpt-5.5 high**

#### Verify (反向 grep)
```bash
# 旧路由应全部清掉
rg -n "Tier1: DeepSeek|DeepSeek V4 Pro.*Tier1|DeepSeek.*Tier1:.*planner|Tier1.*DeepSeek.*planner|deepseek.*plan.*默认|默认.*deepseek.*plan" \
  "G:/ai-toolkit/skills/_shared/" 2>/dev/null
echo "EXPECT_EXIT_0_ONLY_IF_ZERO_HIT"

# 新路由应落地
rg -n "Tier1.*Codex|Codex.*plan.*high|Codex gpt-5\.5.*high|DeepSeek V4 Pro.*审 PLAN" \
  "G:/ai-toolkit/skills/_shared/MODEL_ROUTING.md" 2>/dev/null
echo "EXPECT_HITS_FOUND_NEW_ROUTING"
```

#### Expect
- 旧路由 grep 命中数 = **0** (Tier1: DeepSeek planner 已不再作为默认)
- 新路由 grep 命中 MODEL_ROUTING.md ≥ 3 处 (Tier1 三个工位)
- §0.6.2 应出现 "出计划 Codex / 审计划 DeepSeek" 的可读描述

#### 反向 case (sanity)
- 旧 baseline 草稿可能含 "deepseek-planner 默认出计划" → 那是上一批 §0.7 step 1 的旧文,本批 §0.7 step 1 改 "Codex 出计划 → DeepSeek 审计划"

#### FAIL 判定
- 任意一处 "Tier1: DeepSeek" 残留 → FAIL (Q-13 swap 未完整)
- 异构底线不一致 (e.g. 出 plan/审 plan 同源) → FAIL (Q-4 严守)

---

### T2-0.2 — Q-13 fallback chain L0/L1/L2

**AC-fallback (Q-17)**

#### Verify
```bash
rg -n "L0.*Codex plan|Codex plan.*L0|L0 理想|L0_ideal|L1.*DEFERRED|DEFERRED.*L1|L1.*deepseek fallback|deepseek fallback.*L1|L2.*单 agent|single agent.*L2" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null
```

#### Expect
- §0.6.2 ⑥ (新增小节) 应有 L0/L1/L2 三态枚举表,且每态有明确的出 plan/审 plan/审 code 三角色
- L0 = Codex plan + DeepSeek review + Codex code review (理想 Tier1)
- L1 = DEFERRED_CODEX_REVIEW.md + tester first + DeepSeek plan + DeepSeek review + 异构 fallback
- L2 = Codex + DeepSeek 都卡 → single agent shell default + warning accept

#### FAIL 判定
- L0/L1/L2 任一态缺失 → FAIL
- L2 标 "warning" 但没说 "accept" → FAIL
- L1 写成 "DeepSeek 自审" → FAIL (异构底线,但 L1 已明示降级 = 可接受,但 L1 文档应标 warning)

---

### T2-0.3 — Q-13a sub_session_id 复用规则

**AC-13a.1**

#### Verify (静态)
```bash
# §0.10.7 应有 sub_session_id 复用规则
rg -n "sub_session_id|sub_session_id.*<pipeline_id>|<pipeline_id>.*sub_session_id|session_id_strategy.*per_pipeline|per_pipeline_one_sub_session_id" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null

# WORKFLOW.md dispatch 段应有 sub_session_id 落地字段
rg -n "sub_session_id|<pipeline_id>" \
  "G:/ai-toolkit/skills/_shared/WORKFLOW.md" 2>/dev/null
```

#### Expect
- SKILL_CORE §0.10.7 (新小节) 含 `sub_session_id = <pipeline_id>` 规则
- WORKFLOW.md dispatch 协议含 sub_session_id 字段,且说明 "跨 provider (OpenAI/DeepSeek) 只统一 orchestrator session id, 不保证 provider 内部 cache 命中"
- ≥ 3 处 `sub_session_id` 命中 (体现 "全员共用" 而非单点)

#### FAIL 判定
- §0.10.7 缺失 → FAIL
- WORKFLOW.md dispatch 段未提 sub_session_id → FAIL (Q-13a 落地执行点)
- 误写成 "DeepSeek 和 Codex 共享 cache" → FAIL (违反 §A-2 跨 provider cache 不保证)

---

### T2-0.4 — Q-13b 500k token threshold

**AC-13b.1**

#### Verify
```bash
rg -n "token_budget_threshold_deepseek|500000 token|<500k|≥500k|>=500k|500k token threshold|DeepSeek.*500k|500k.*DeepSeek" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null
```

#### Expect
- §0.7.2 返工分情况表新增一行:`DeepSeek context < 500k → 可返工一轮 / ≥ 500k → 主编排判定拆新 pipeline`
- §0.10.8 (新) 或 §0.7.2 备注:**"500k = 用户粗粒度规则, 实际 DeepSeek 端 context 阈值可能不同"** caveat
- threshold 字段既可写 `<500k` 也可写 `500000 token` (任一等价)

#### FAIL 判定
- 返工表只有 4 行 (缺 500k threshold 行) → FAIL
- threshold 写 `<250k` (用了 Codex 阈值混搭) → FAIL (Q-13b 特指 DeepSeek)

---

### T2-0.5 — Q-13c token_usage 报告

**AC-13c.1/13c.2**

#### Verify
```bash
rg -n "token_usage|token 报告|token_usage.*明细|sub-agent.*token|批后.*token|批后 token 报告" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null

rg -n "token_usage|token_usage.*明细" \
  "G:/ai-toolkit/skills/_shared/" 2>/dev/null | rg -i "template|implementation_report"
```

#### Expect
- §0.10.8 (新) 有 `token_usage` 报告规则:每批完成后 IMPLEMENTATION_REPORT.md 末尾 + ACCEPTANCE 时列 sub-agent session token_usage 明细 (含 reviewer 65640 tokens / 15 tool_uses / 292s 这类格式)
- 模板或 IMPLEMENTATION_REPORT 末尾示例段含 token_usage 字段 (developer 写报告时填实际值)

#### FAIL 判定
- §0.10.8 缺失 token_usage 报告要求 → FAIL
- 模板未列 token_usage 字段 → FAIL (Q-13c 落地兜底)
- 写成 "show_session_context.py 自动汇总" 但不写到 IMPLEMENTATION_REPORT 末尾 → 半 FAIL (具体看是否 §0.10.8 有要求写)

---

### T2-1.1 — Q-1 DEFERRED + tester first 7 步路径

**AC-1.1**

#### Verify
```bash
rg -n "DEFERRED_CODEX_REVIEW\.md|DEFERRED_due_to_codex_unavailable|deferred_due_to_codex_unavailable|reviewer_status.*deferred|跳过 PLAN_REVIEW|skip.*PLAN_REVIEW|tester first|tester-first" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null

# 验证 §0.7.2 7 步路径完整存在
rg -n "1\. 写 DEFERRED_CODEX_REVIEW|2\. \*\*不解锁 developer\*\*|3\. 直接派 \[tester:minimax\]|tester 必派|4\. developer 实现|5\. tester 跑测试|6\. reviewer 审 diff|7\. ACCEPTANCE" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null
```

#### Expect
- §0.7.2 含完整 7 步路径 (DEFERRED 写 → 不解锁 developer → 直接派 tester 写 TEST_TARGET.md → developer 实现 → tester 跑测试 → reviewer (异构底线对 code review 宽松) → ACCEPTANCE)
- `DEFERRED_due_to_codex_unavailable` 三态枚举合法结局列出 (§0.7.1 维持)

#### FAIL 判定
- §0.7.2 7 步缺失任一步 → FAIL
- §0.7.2 写成 "Codex 卡死 → 降级 deepseek-reviewer 假装异构" → FAIL (异构底线)
- 三态枚举删了 DEFERRED 态 → FAIL

---

### T2-1.2 — Q-2 返工分情况表 (覆盖 4 行 + 500k 行)

**AC-2.1**

#### Verify
```bash
# 4 行覆盖: Codex 有/无额度 × 首次/返工
rg -n "首次 PLAN.*Codex 有额度|首次 PLAN.*Codex 卡死|返工 PLAN_PATCH.*Codex 有额度|返工 PLAN_PATCH.*Codex 卡死|Tier2 角色翻转|DEFERRED.*skip.*tester first" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null

# 500k 新行 (Q-13b)
rg -n "DeepSeek.*<500k|<500k.*返工|≥500k.*新 pipeline|>=500k.*新 pipeline|500k.*新 pipeline" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null
```

#### Expect
- §0.7.2 返工周期表**维持 4 行** (Codex 有/无 × 首次/返工)
- §0.7.2 返工表**新增 1 行** (Q-13b 500k threshold):DeepSeek context < 500k → 可返工 / ≥ 500k → 拆新 pipeline
- 或 §0.7.2 + §0.10.8 之间通过跨章节引用

#### FAIL 判定
- 4 行变 3 行 (缺首次或返工) → FAIL
- 500k 行不在返工表 → FAIL (Q-13b 必须落地)

---

### T2-1.3 — Q-3 PLAN_REVIEW 三态枚举保持

**AC-3.1**

#### Verify
```bash
rg -n "APPROVE|REQUEST_CHANGES|DEFERRED_due_to_codex_unavailable" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null | rg "0\.7\.1|三态|合法结局|合法状态"
```

#### Expect
- §0.7.1 三态枚举表维持三行,顺序可调,但 DEFERRED_due_to_codex_unavailable 必须保留
- 上一批 §0.7.1 已有此表,本批**只允许微调措辞**,不得删行

#### FAIL 判定
- 三态任一缺失 → FAIL (Q-3)
- 新增第四态 (e.g. APPROVE_WITH_CONDITIONS) → 视 reviewer 审, 默认 WARN

---

### T2-1.4 — Q-4 异构性自纠错 (4 字段 a/b/c/d)

**AC-4.1**

#### Verify
```bash
rg -n "异构性自纠错|异构底线|异构已破|planner\.model.*reviewer\.model|reviewer\.model.*planner\.model|PLAN_REVIEW 工位异构底线|CODE_REVIEW 工位.*宽" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null
```

#### Expect
- §0.6.2 ⑤ 维持或强化:**4 个子字段**:
  - (a) 案例: deepseek-reviewer 审 deepseek-planner → 异构已破
  - (b) 主编排 self-check: 派 reviewer 前确认 `planner.model != reviewer.model`
  - (c) 异构已破 → 立即回滚, 不事后加注
  - (d) PLAN_REVIEW 工位异构底线 **严于** CODE_REVIEW 工位

#### FAIL 判定
- (b) `planner.model != reviewer.model` 字段缺失 → FAIL (异构底线 contract)
- (d) 双工位异构底线区分未明 → WARN,看 reviewer 判定
- (c) 写 "写 PLAN_REVIEW_RESOLUTION 补救" → FAIL (反模式:事后加注)

---

### T2-2.1 — Q-5 INTERRUPT_AND_RE_PLAN + DETECT_CONTRADICTION

**AC-5.x**

#### Verify
```bash
rg -n "INTERRUPT_AND_RE_PLAN|DETECT_CONTRADICTION|CONTRADICTION|UNRELATED|DEFERRED|需求.*不明确.*追问|echo 追问|不派任何 sub-agent|不派任何 sub-agent" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null
```

#### Expect
- §0.10 ⑤ (现 §0.10 ⑤) 含 **INTERRUPT_AND_RE_PLAN** operator 描述,与 SendMessage tool 协同
- §0.10 ⑥ (现 §0.10 ⑥) 含 **DETECT_CONTRADICTION** 描述,4 类判定:CONTRADICTION / UNRELATED / DEFERRED / 含糊→追问
- 判定算法 (主编排当下 turn self-check) 含 6 步,最后一步"含糊→不派 sub-agent"

#### FAIL 判定
- ⑤ ⑥ 任一缺失 → FAIL (Q-5 双 operator 必须齐)
- 判定算法简化为 "case by case" → WARN
- "echo 追问" 字段缺失 → WARN (Q-6 关联)

---

### T2-2.2 — Q-6 case A 主编排自判 / case B 主编排代问

**AC-6.x**

#### Verify
```bash
rg -n "case A|case B|主编排自判|主编排代 sub-agent 问|AMBIGUITY_RAISED|sub-agent.*不直接调 user|不直接调 AskUserQuestion|不直接调.*user-facing" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null
```

#### Expect
- §0.11.1 维持两路径:case A 主编排自行判定 + case B sub-agent 通过 `AMBIGUITY_RAISED` 回报,主编排代问
- sub-agent protocol 强化:不允许直接调 user-facing tool (AskUserQuestion 类似)
- **反模式**段必须含两条:不要等 sub-agent 反馈 "需求不清";不要让 sub-agent 直接调 user

#### FAIL 判定
- 只有 case A 没有 case B → FAIL (Q-6 双路径必须齐)
- sub-agent protocol 强化段缺失 → FAIL (Q-6 protocol 强制)

---

### T2-2.3 — Q-7 USER_NEEDS_DIGEST.md 协议

**AC-7.x**

#### Verify
```bash
rg -n "USER_NEEDS_DIGEST\.md|USER_NEEDS_DIGEST|raw.*digest.*unknowns|raw 原话|用户原话逐字|主编排整理后的清晰需求" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null
```

#### Expect
- §0.11.2 协议段含 3 要素:raw (用户原话逐字) + digest (主编排整理清晰需求, 按主题分组, 标 priority) + 已知未澄清
- 文件位置: `docs/<skill>/<date-task>/USER_NEEDS_DIGEST.md` 与 `PLAN.md` 同目录
- sub-agent 用法: 先读 raw + digest 再写 PLAN

#### FAIL 判定
- 三要素任一缺失 → FAIL (raw / digest / unknowns 缺一不可)
- 文件位置写错 (e.g. `.ai-work/runs/`) → WARN

---

### T2-2.4 — Q-12 file overlap 集合论 O(N) 算法

**AC-12.1**

#### Verify
```bash
rg -n "file overlap|文件重叠|集合论|O\(N\)|共享文件|依赖方向|并行限制|file-overlap.*聚类|聚类.*算法" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null
```

#### Expect
- §0.10 ⑥ (DETECT_CONTRADICTION 之后, 也可能在 §0.9 + §0.11) 有 file overlap 聚类算法段
- 集合论 O(N) 描述或可执行规则:共享文件 → 同类 / 串行依赖;不同文件 + 低耦合 → 并行
- "file overlap 聚类" 标题或相同含义短语 ≥ 1 处

#### FAIL 判定
- 算法段仅有概念描述, 无具体可执行规则 → WARN (reviewer 判定)
- §0.10 ⑥ (DETECT_CONTRADICTION) 改为 file overlap 算法而 ⑥ 不存在 → FAIL

---

## 4. P1 — 推荐测 (非阻塞,warn 级别)

### T2-3.1 — Q-8 流水线并行/串行柔性化

**AC-8.1/8.2/8.3**

#### Verify
```bash
rg -n "CHAIN_AFTER|PARALLEL_NEW_PIPELINE|耦合度高|耦合度低|同类串行|不同类.*并行|柔性化" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null
```

#### Expect
- §0.10 4 个 operator 维持:REQUEUE / ABORT_TO_PLAN / PARALLEL_NEW_PIPELINE / CHAIN_AFTER
- §0.9 + §0.10 包含 "同类串行,不同类低耦合才并行" 规则
- Q-8 要求 spec: 耦合度高 = CHAIN_AFTER / 耦合度低 = PARALLEL_NEW_PIPELINE

#### FAIL 判定
- 4 operator 缺一 → FAIL (上批 baseline)
- "并行/串行柔性化" 规则段缺失 → WARN

---

### T2-3.2 — Q-9 主编排疏漏接受 + 主 session 不阻塞

**AC-9.1/9.2**

#### Verify
```bash
rg -n "always receptive|疏漏接受|可被用户插话纠正|主 session.*不阻塞|不阻塞主 session|run_in_background|background.*规范|不阻塞.*主 session|主 session.*永远 receptive" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null
```

#### Expect
- §0.6.1 ④ + §0.8 + §0.11 包含 "主编排疏漏可被用户插话纠正"
- §0.8 维持 "background sub-agent 不阻塞主 session" 5 条规则:派必须 background / 派完立刻释放 / 完成时 harness 自动 inject / 用户问时主动回报 / 主 session 不能独占 turn
- §0.11 含 "主编排者永远 receptive"

#### FAIL 判定
- "主 session 永远 receptive" 缺失 → FAIL (上批 Q-9 已加)
- §0.8 background 规范任一条缺失 → WARN

---

### T2-3.3 — Q-10 idle classifier

**AC-10.1/10.2**

#### Verify
```bash
rg -n "idle classifier|idle-time classifier|空闲|等待后台|等待用户|blocked|可推进|idle-state|idle.*状态|idle.*枚举" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null
```

#### Expect
- §0.8 + §0.11 含 idle classifier 多态枚举:空闲 / 等待后台 / 等待用户 / blocked / 可推进
- 每态必须有 trigger + 动作

#### FAIL 判定
- classifier 缺失 → WARN (Q-10 是 nice-to-have 落实,可借 §0.8.④ 用户问时回报)
- 多态 < 3 态 → WARN

---

## 5. 跨文件 + 集成 — 必测

### T2-4.1 — Q-11 长而清命名规则 + 跨文件引用

**AC-11.1/11.2**

#### Verify (跨 3 文件)
```bash
# 1. SKILL_CORE §0.11 命名规则段
rg -n "命名规则|长而清|全词或中文|禁缩写|task_id.*category.*pipeline.*dispatch label" \
  "G:/ai-toolkit/skills/_shared/SKILL_CORE.md" 2>/dev/null

# 2. auto-dev/SKILL.md 入口摘要引用
rg -n "命名规则|长而清|全词或中文|category" \
  "G:/ai-toolkit/skills/auto-dev/SKILL.md" 2>/dev/null

# 3. WORKFLOW.md CATEGORY_DISCOVERY 引用
rg -n "命名规则|长而清|全词或中文|category" \
  "G:/ai-toolkit/skills/_shared/WORKFLOW.md" 2>/dev/null
```

#### Expect
- SKILL_CORE §0.11 新增 "命名规则段",含正反例 (e.g. `skill-meta-flow-control-rules-extended-2026-07-10` 是好例,`sm-fce-2610710` 是坏例)
- auto-dev/SKILL.md 入口摘要引用命名规则 + category 字段
- WORKFLOW.md CATEGORY_DISCOVERY 段也引用命名约束

#### FAIL 判定
- 命名规则段缺失 → FAIL (Q-11 P0 必落)
- 3 文件同步失败 (只 SKILL_CORE 有, 入口摘要无) → FAIL (Q-11 跨文件)
- 命名段未含 "禁缩写" → WARN,reviewer 判定

---

### T2-5.1 — 集成反向 grep (旧路由残留)

**集成验证,反向 grep**

#### Verify
```bash
# 整个 _shared + auto-dev 目录 旧路由/旧模型残留检查
rg -n "GPT-5\.4|gpt-5\.4|GPT-5\.4 high|gpt-5\.4 high|DS-out|first.*DS.*out|第一轮.*deepseek.*plan" \
  "G:/ai-toolkit/skills/_shared/" \
  "G:/ai-toolkit/skills/auto-dev/" 2>/dev/null
echo "EXPECT_EXIT_0_ONLY_IF_ZERO_HIT"

# 旧 "Tier1: DeepSeek planner" 残留
rg -n "Tier1: DeepSeek|DeepSeek.*Tier1.*planner|deepseek.*planner.*Tier1" \
  "G:/ai-toolkit/skills/_shared/" \
  "G:/ai-toolkit/skills/auto-dev/" 2>/dev/null
echo "EXPECT_EXIT_0_ONLY_IF_ZERO_HIT"

# 残留"GPT-5.4 first round / 第一轮审查"在 docs 沉淀目录
rg -n "GPT-5\.4|gpt-5\.4|first.*GPT-5\.4" \
  "G:/ai-toolkit/docs/auto-dev/2026-07-10-skill-meta-flow-control-rules-extended/" 2>/dev/null
echo "EXPECT_EXIT_0_ONLY_IF_ZERO_HIT_DOCS"
```

#### Expect
- 所有反向 grep 命中数 = **0** (本批应全部清除上一批残留的旧 GPT-5.4 / 旧 Tier1)
- **例外**: 历史沉淀目录 `2026-07-09-skill-meta-tdd-flow/` 是记录,允许保留 (历史 commit 不可改);本批沉淀目录应 0 命中

#### FAIL 判定
- `_shared/` 或 `auto-dev/` 任一命中 → FAIL (残留)
- 本批沉淀目录命中 → FAIL

---

### T2-5.2 — forbidden scope 严守 (PLAN.md 不列禁改文件作目标)

#### Verify
```bash
rg -n "install-all\.ps1|manifest\.json|nested-submodule-restructure" \
  "G:/ai-toolkit/docs/auto-dev/2026-07-10-skill-meta-flow-control-rules-extended/PLAN.md" 2>/dev/null
echo "EXPECT_EXIT_0_ONLY_IF_ZERO_HIT (if forbidden scope listed as in-scope, that's wrong)"
```

#### Expect
- PLAN.md 提到 `install-all.ps1` / `manifest.json` / `nested-submodule-restructure` 时,语境必须是 "**不进 scope**" / "forbidden" / "明确不进本批"
- 命中数 = 0 表示 PLAN.md 完全不提这些文件 = OK
- 命中且语境是 in-scope → **FAIL** (本批不能改这些文件)

#### FAIL 判定
- PLAN.md 把 forbidden 文件列为修改目标 → FAIL (违反 PLAN.md §3 + §8 非目标)

---

### T2-5.3 — Q-13a dispatch 落地 (行为验证)

**AC-13a.1 落地行为验证**

#### Set-up
- `dispatch.ps1` 已有 `-SessionId` 参数 + `[dispatch] 派 [...] action=... model=... effort=... session={SessionId}` echo (`shared/scripts/dispatch.ps1` line 43 / 98-99 / 105 已实现)
- 本批验证: 真跑一条 dispatch,看 echo 是否含 session=

#### Verify (shell run)
```bash
# 用 fake session 跑一次 dispatch (mock),捕获 stdout
SID="skill-meta-flow-control-rules-extended-2026-07-10"
pwsh -File "G:/ai-toolkit/skills/_shared/scripts/dispatch.ps1" \
  -Action codex-plan \
  -Model gpt-5.5 \
  -Effort high \
  -SessionId "$SID" \
  -ProjectRoot "G:/ai-toolkit" \
  -TaskDir "G:/ai-toolkit/.ai-work/runs/skill-meta-flow-control-rules-extended-2026-07-10" \
  -Prompt "sentinel-check-from-tester-only-no-side-effect" \
  2>&1 | tee /tmp/dispatch-t253.log

echo "---expected line---"
grep -E "\[dispatch\] 派 \[.*\] action=.* session=$SID" /tmp/dispatch-t253.log
echo "EXIT: $?"
```

#### Expect
- stdout 含一行:`[dispatch] 派 [...] action=codex-plan model=gpt-5.5 effort=high session=skill-meta-flow-control-rules-extended-2026-07-10 project=... task-dir=...`
- session= 后面跟的就是 Q-13a 的 sub_session_id 字面值
- 字段顺序: action= / model= / effort= / **session=** / project= / task-dir= (按现有 dispatch.ps1 实现)
- 即使上游 Codex 卡死, dispatch 入口行为仍正确 (echo session= 是必需)

#### Tolerate (不全 fail)
- 真跑会触发 Codex CLI 卡死 (L0 fallback active 中), 若 dispatch 在 call Code CLI 之前先 echo session 字段 → OK
- 若 Codex 端真卡死导致 echo 没出 → 上 sentinel 是 unit-level,允许标 `WARN-no-echo-yet` 交 developer 阶段验证

#### FAIL 判定
- `-SessionId` 参数缺失 (line 43 已声明,本批不改 source,默认在) → 行为已存在 = PASS
- echo 含 session= 字段缺失 → FAIL (Q-13a 落地契约)

---

## 6. 集成回归 (test runner 命令)

> 跑完 T2-0..T2-5 后,执行回归测试确认 baseline 规则未破坏。

```bash
# ===== A. scripts 自检 =====
python "G:/ai-toolkit/skills/_shared/scripts/test_show_session_context.py"
echo "EXIT_A: $?  (expect 0)"
python "G:/ai-toolkit/skills/_shared/scripts/test_auto_dev_guard.py"
echo "EXIT_B: $?  (expect 0)"

# ===== B. 全文件 grep 旧路由 / 旧模型残留 =====
rg -n "GPT-5\.4|gpt-5\.4|Tier1: DeepSeek|DeepSeek.*Tier1.*planner" \
  "G:/ai-toolkit/skills/_shared/" \
  "G:/ai-toolkit/skills/auto-dev/" 2>/dev/null
echo "EXIT_C: $?  (expect 0 = no hits)"

# ===== C. forbidden scope 检查 =====
rg -n "install-all\.ps1|manifest\.json|nested-submodule" \
  "G:/ai-toolkit/docs/auto-dev/2026-07-10-skill-meta-flow-control-rules-extended/PLAN.md" 2>/dev/null
echo "EXIT_D: $?  (expect 1 = no hits or hits only in 'not in scope' context; 视 grep exit code)"

# ===== D. WORKFLOW.md dispatch 段 sub_session_id 检查 =====
rg -n "sub_session_id" "G:/ai-toolkit/skills/_shared/WORKFLOW.md" 2>/dev/null
echo "EXIT_E: $?  (expect 0 = at least 3 hits)"

# ===== E. dispatch.ps1 [dispatch] echo 实地跑 =====
SID="skill-meta-flow-control-rules-extended-2026-07-10"
pwsh -File "G:/ai-toolkit/skills/_shared/scripts/dispatch.ps1" \
  -Action codex-plan -Model gpt-5.5 -Effort high -SessionId "$SID" \
  -ProjectRoot "G:/ai-toolkit" \
  -TaskDir "G:/ai-toolkit/.ai-work/runs/skill-meta-flow-control-rules-extended-2026-07-10" \
  -Prompt "sentinel-only" 2>&1 | grep -E "\[dispatch\]"
echo "EXIT_F: $?  (expect 0 = dispatch echo present)"
```

---

## 7. 已知 gap 不在本批 fix

> **Note to developer**: 这些是本批已 identified 但**不在 plan.meta.json files_in_scope** 内的项,留给后续批次。

| 已知 bug / gap | 位置 | 影响 | 计划归属 |
|---|---|---|---|
| `_codex-runtime.ps1:257-260` `codex exec ... resume <id>` 语法 bug | `_shared/scripts/_codex-runtime.ps1` (本批不读,推测存在) | Codex 派单 exit -1 但 output_bytes > 0 误报 fail | 后续批修;本批**不**列入 files_in_scope,理由:本批只改 SKILL_CORE + MODEL_ROUTING + WORKFLOW + auto-dev/SKILL.md (4 文件) |
| 上一批 T10 install gap | `~/.claude/settings.json` 缺 PostToolUse hook | PostToolUse handler 未 register | 跑 `pwsh -File G:\ai-toolkit\install-all.ps1 -Framework claude` 重装;**不在本批代码 scope** |
| sub-agent protocol 强化需 `auto_dev_guard.py` 改 | `_shared/scripts/auto_dev_guard.py` | 本批 §0.11 case B protocol 需要 hook 端 grep AMBIGUITY_RAISED | 留 R-LOW-2 / 下一批 |

---

## 8. self-check echo (写完时由 tester agent 输出)

```
[tester:minimax] TEST_TARGET.md done.
path=G:\ai-toolkit\docs\auto-dev\2026-07-10-skill-meta-flow-control-rules-extended\TEST_TARGET.md
test_count=20 (T2-0.1..T2-5.3)
test_categories:
  Q-13 × 5  -> T2-0.1 + T2-0.2 + T2-0.3 + T2-0.4 + T2-0.5
  Q-1 × 4   -> T2-1.1 + T2-1.2 + T2-1.3 + T2-1.4
  Q-5..12  -> T2-2.1 (Q-5) + T2-2.2 (Q-6) + T2-2.3 (Q-7) + T2-2.4 (Q-12)
  Q-8..10   -> T2-3.1 + T2-3.2 + T2-3.3
  Q-11      -> T2-4.1
  集成 × 3  -> T2-5.1 (旧路由残留) + T2-5.2 (forbidden scope) + T2-5.3 (dispatch 行为)
P0_tests=T2-0.1 T2-0.2 T2-0.3 T2-0.4 T2-0.5 T2-1.1 T2-1.2 T2-1.3 T2-1.4 T2-2.1 T2-2.2 T2-2.3 T2-2.4 T2-4.1 T2-5.1 T2-5.2 T2-5.3 (17 个)
P1_tests=T2-3.1 T2-3.2 T2-3.3 (3 个)
ac_coverage=17/17 (100%)
sub_session_id=skill-meta-flow-control-rules-extended-2026-07-10 (Q-13a 共用)
known_gaps=3 (_codex-runtime.ps1:257-260 + 上一批 T10 + auto_dev_guard.py 协议强化)
next_stage=developer:minimax TDD implementation
```

---

## 9. TOKEN_USAGE_REPORT_TEMPLATE

> 后续 developer / tester / reviewer 完成本批后,在 `IMPLEMENTATION_REPORT.md` 末尾 + ACCEPTANCE 时填以下模板 (Q-13c 落地)。

```
## Token Usage Report (Q-13c)

| sub-agent | role | session_id | model | effort | input_tokens | output_tokens | total_tokens | tool_uses | elapsed_seconds | files_touched |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| [planner:codex] | planner | skill-meta-flow-control-rules-extended-2026-07-10 | gpt-5.5 | high | TBD | TBD | TBD | TBD | TBD | PLAN.md + plan.meta.json |
| [reviewer:deepseekV4pro] | plan_reviewer | skill-meta-flow-control-rules-extended-2026-07-10 | fable | max | 65640 | TBD | 65640+ | 15 | 292 | PLAN_REVIEW.md |
| [developer:minimax] | developer | skill-meta-flow-control-rules-extended-2026-07-10 | minimax | high | TBD | TBD | TBD | TBD | TBD | _shared/SKILL_CORE.md + _shared/MODEL_ROUTING.md + _shared/WORKFLOW.md + skills/auto-dev/SKILL.md |
| [tester:minimax] | tester (write) | skill-meta-flow-control-rules-extended-2026-07-10 | minimax | medium | TBD | TBD | TBD | TBD | TBD | TEST_TARGET.md + TEST_REPORT.md |
| [tester:minimax] | tester (run) | skill-meta-flow-control-rules-extended-2026-07-10 | minimax | low | TBD | TBD | TBD | TBD | TBD | TEST_REPORT.md + TEST_REPORT.summary.md |
| [reviewer:codex] | code_reviewer | skill-meta-flow-control-rules-extended-2026-07-10 | gpt-5.5 | high | TBD | TBD | TBD | TBD | TBD | diff.patch |

**pipeline_sub_session_id** = skill-meta-flow-control-rules-extended-2026-07-10 (Q-13a 全员共用)
**500k_threshold_status** = DeepSeek round input context = <500k / >=500k (TBD on actual run)
**fallback_chain_actual** = L0_ideal (Codex 真成功) / L1_fallback / L2_single_agent (TBD)
```

### 字段说明
- `input_tokens` / `output_tokens` / `total_tokens`: 来自 `show_session_context.py` 每角色 dispatch 时 record
- `tool_uses`: sub-agent 内部 Bash/Read/Write/Edit 调用次数
- `elapsed_seconds`: dispatch → structured report 返回时长
- `files_touched`: 该 sub-agent 改/写的文件路径列表

---

## 10. 边界与 don'ts

- **只 Write 本文件** (`docs/auto-dev/2026-07-10-skill-meta-flow-control-rules-extended/TEST_TARGET.md`) — 流程产物,不算 skill 系统输出
- **不要** git add / git commit (本批沉淀目录文件不 commit,留给 orchestrator 阶段)
- **不要** Edit / Write `_shared/`, `auto-dev/`, `auto-code-android-dev/` 任何 src 文件
- **不要** 派其它 sub-agent (本次只 Write 单文件)
- **不要** Read 无关文件 (uconline to PLAN.md / PLAN_REVIEW.md / plan.meta.json / USER_NEEDS_DIGEST.md / AMBIGUITY_RAISED.md / DEFERRED_CODEX_REVIEW.md / SKILL_CORE.md 现有章节确认 / MODEL_ROUTING.md / WORKFLOW.md / auto-dev/SKILL.md 入口 / 上一批 TEST_TARGET.md + TEST_REPORT.summary.md 模板)
- **不要** 重复跑 deepseek-reviewer 已 evaluation 过的 PLAN.md review (PLAN_REVIEW.md 已代写)

---

**END OF TEST_TARGET.md**
