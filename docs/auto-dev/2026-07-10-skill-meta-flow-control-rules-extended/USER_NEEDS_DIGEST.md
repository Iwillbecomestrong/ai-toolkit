# USER_NEEDS_DIGEST.md — skill-meta-flow-control-rules-extended 第二批

> 这是流程产物。主编排写,给本批 planner / developer / tester / reviewer sub-agent 提供 raw + digest 视角。
> 继承并扩展上一批 USER_NEEDS_DIGEST.md 内容。

---

## A. 用户原始 raw

### A.0 继承自上一批 (R-1 ~ R-15)
见 `docs/auto-dev/2026-07-09-skill-meta-tdd-flow/USER_NEEDS_DIGEST.md` 第 12-72 行。本批不再重复,所有 R-N 都仍是 effective 状态。

### A.1 上一批 NEXT_ACTIONS.md 里 Q-1 ~ Q-12 用户原话
继承 `docs/auto-dev/2026-07-09-skill-meta-tdd-flow/NEXT_ACTIONS.md` 第 7-183 行。

### A.2 Q-13 用户原话（本批新增模型路由 swap + session 复用 + token budget）

#### A.2.1 Q-13 主线（用户在回话里给的修正）
> "我觉得是不是可以最开始就让一开始就应该是让 gpt5.5 来做计划，然后 deepseekV4pro 来审核计划如果有补充就让 gpt 原会话来查看是不是要补充，最后还是 gpt5.5 还审查代码呢。试一下这个逻辑咋样。就是把第二轮事情提到第一轮争取一次通过"

#### A.2.2 Q-13a 用户原话（session 复用 + cache）
> "就是前面做计划的那个会员。一直沿用同一个会话复用缓存率。codex 的 gpt 和 deepseek 在同一批会话的子代理角色中（无论怎么变），始终用同一个会话。"

#### A.2.3 Q-13b 用户原话（DeepSeek context < 500k 来一轮）
> "deepseek 如果一轮需求结果的上下文占用了小于 <500k 还可以在来一轮。"

#### A.2.4 Q-13c 用户原话（批后 token 占用报告）
> "所以在一批需求完成之后，要汇报一下子代理会话的一个 token 占用情况。"

#### A.2.5 Q-13 fallback chain 用户原话
> "(α) Q-13 作为「理想 Tier1」落地 §0.6.2/§0.7；Q-1 「Codex 卡死 → DEFERRED + tester first」作为 fallback 独立存在（两条并存，现实跑 Q-1 fallback，文档两套都有）如果没有的话就只退化成 deepseek 做计划不审查。"

---

## B. 主编排 digest (Q-1..Q-13 整理后)

### B-1. 流程顺序类 (Q-1, Q-2, Q-3, Q-4) — §0.6 / §0.7
1. **Q-1 Codex 卡死 → DEFERRED + tester first** (R-9)
2. **Q-2 返工周期分情况** (R-10)
3. **Q-3 PLAN_REVIEW 三态枚举**
4. **Q-4 异构性自纠错**

### B-2. 用户插话 / 判定类 (Q-5, Q-6, Q-7, Q-12) — §0.10 / §0.11
5. **Q-5 插话自动判定 4+2 operator**（DETECT_CONTRADICTION + INTERRUPT_AND_RE_PLAN）
6. **Q-6 主编排当下判定时机** (case A 自判 / case B 代 sub-agent 问)
7. **Q-7 USER_NEEDS_DIGEST.md 协议**
12. **Q-12 file overlap 聚类算法**（集合论 O(N)）

### B-3. 主 session 永远 receptive 类 (Q-8, Q-9, Q-10) — §0.8 / §0.10
9. **Q-8 流水线并行/串行柔性化**
10. **Q-9 主编排疏漏接受 + 不阻塞**
11. **Q-10 idle classifier**

### B-4. 命名规则类 (Q-11) — §0.11 + 跨文件
12. **Q-11 长而清命名**

### B-5. NEW — 模型路由 swap + session 复用 (Q-13) — §0.6.2 / §0.7 / §0.10
13. **Q-13 Tier1 swap 主路由**：Codex gpt-5.5 高做 PLAN → deepseekV4Pro max 审 PLAN → Codex 审 CODE（Tier1 全 swap，与之前 §0.6.2 反向）
14. **Q-13a session 复用规则**：同一 batch（pipeline）内，所有 sub-agent 必须沿用同一 session ID（无论角色 planner/developer/tester/reviewer 怎么变），cache 复用最大化
15. **Q-13b DeepSeek token budget**：DeepSeek 单轮上下文占用 < 500k token → 允许再来一轮（返工）；≥ 500k → 强制开新 pipeline（避免 context 爆炸）
16. **Q-13c 批后 token 报告**：每批需求完成 → 主编排 / IMPLEMENTATION_REPORT 末尾报告 sub-agent session token 占用明细
17. **Q-13 fallback chain**：
    - L0（理想 Tier1）：Codex plan + DeepSeek review + Codex code review
    - L1（Codex 卡死）：Q-1 DEFERRED → tester first + DeepSeek plan → DeepSeek review (异构底线 fallback, 标 warning)
    - L2（Codex + DeepSeek 都卡）：单 agent shell default → plan，不审 (warning + accept) — 极 fallback

---

## C. 未澄清 / 自相矛盾 (供本批 planner 留意)

### C-1. "Codex 现在有额度" 不稳定（继承上一批 C-1，仍 open）
### C-2. "Codex 何时回来" — 用户未明示。当前假设：Codex 一直不可用直到 exit -1 status=completed。本批跑 L1 fallback，文档两套都有。
### C-3. "每 3 需求最多 1 pipeline" 与 Q-8 算法关系
### C-4. Q-11 命名规则 "长" 多长
### C-5. sub-agent 后台跑不阻塞 vs TDD 流程不能跳过
### C-6. Q-13 session 复用 cache 跨 model 落地机制（Open Q）
- Codex (OpenAI) 和 DeepSeek (via litellm to deepseek-v4-pro) 是**两个不同 model provider**。
- "同一 session" 在 orchestrator 视角 = **同 session ID / 同 .ai-work/runs/<id>/ 目录 / 同 SUB_SESSION_ID**（dispatch 时回填）。
- Codex 端 cache 由 OpenAI 维护；DeepSeek 端 cache 由 litellm / DeepSeek 端维护。
- "缓存率 (cache rate)" 指 **provider 内部 prompt cache 命中率**，两个 provider 各自维护 → 节省 token + 加速推断。
- 落地方式：subagent dispatch 时填 `sub_session_id` = `<pipeline_id>` (Q-N 续 → 同一 ID)，所有 sub-agent 不分角色用同一 `<pipeline_id>`。
### C-7. Q-13b "500k token threshold" 测不准
- "<500k 还可以在来一轮" 是粗粒度规则，实际每个 model 的 context window 不同。
- DeepSeek V4 Pro 典型 context = 200k token 输入；用户说"<500k 来一轮" 可能是**输入 context 占用** 或 **round 累计 token**。
- 本批按"**单轮 DeepSeek sub-agent 输入 context < 500k token**"实现；如果实际 DeepSeek 端报 token_usage > 500k → 主编排判定是否拆新 pipeline。

---

## D. 文件 scope（Q-8 聚类结果 + Q-13 修订）

所有 13 个 Q 全部主改 SKILL_CORE.md：

| Q | 主要 files_modify | 章节 |
|---|---|---|
| Q-1 | `_shared/SKILL_CORE.md` | §0.7.2 |
| Q-2 | `_shared/SKILL_CORE.md` | §0.7.2 |
| Q-3 | `_shared/SKILL_CORE.md` | §0.7.1 |
| Q-4 | `_shared/SKILL_CORE.md` | §0.6.2 ⑤ |
| Q-5 | `_shared/SKILL_CORE.md` | §0.10 ⑤⑥ + §0.11 |
| Q-6 | `_shared/SKILL_CORE.md` | §0.11 |
| Q-7 | `_shared/SKILL_CORE.md` | §0.11 |
| Q-8 | `_shared/SKILL_CORE.md` | §0.9 + §0.10 |
| Q-9 | `_shared/SKILL_CORE.md` | §0.6 + §0.8 + §0.11 |
| Q-10 | `_shared/SKILL_CORE.md` | §0.8 + §0.11 |
| Q-11 | `_shared/SKILL_CORE.md` + `_shared/SKILL.md` + `_shared/WORKFLOW.md` | §0.11 + 跨引用 |
| Q-12 | `_shared/SKILL_CORE.md` | §0.10 + §0.11 |
| **Q-13** | **`_shared/SKILL_CORE.md` + `_shared/MODEL_ROUTING.md`** | **§0.6.2 + §0.7 + §0.10 (新)** |

**Q-13 修订后聚类结论**: 13 Q 全部高耦合于 SKILL_CORE.md → 1 个 pipeline (CHAIN_AFTER 进本批，C-4 决策)。

---

## E. Q-13 详细落地清单（planner 必须展开）

### E-1. §0.6.2 MODEL_ROUTING 主表（必改）

| 项 | 旧 | 新（Q-13 落地） |
|---|---|---|
| Tier1 出 PLAN | deepseekV4Pro (max) | **Codex gpt-5.5 (high)** |
| Tier1 审 PLAN | Codex (high) | **deepseekV4Pro (max)** |
| Tier1 审 CODE | deepseekV4Pro | **Codex gpt-5.5 (high)** |
| Tier2（返工） | Codex 出 + deepseek 审 | deepseek 出 + Codex 审（**角色翻转**对应新 Tier1） |

新增 fallback chain L1/L2（如 B-5 17 描述）。

### E-2. §0.7 PLAN_REVIEW 工位规则（必改）

- §0.7.1 三态枚举保持（APPROVE / REQUEST_CHANGES / DEFERRED_due_to_codex_unavailable）
- §0.7.2 返工分情况表加新行（Q-13b 500k threshold + Q-13a session 复用）

### E-3. §0.10 新增 §0.10.x — session 复用 + token 报告

- **§0.10.7 session 复用**：subagent dispatch 时必须回填 `sub_session_id = <pipeline_id>`；同一 pipeline 内所有 sub-agent 无差别用同一 `<pipeline_id>`。
- **§0.10.8 token budget 报告**：IMPLEMENTATION_REPORT.md 末尾 + ACCEPTANCE 时 → 列 sub-agent session token_usage 明细（哪一段占多少），user 验收可看。

### E-4. 跨文件引用

- `_shared/MODEL_ROUTING.md`：与 §0.6.2 同步；表头加 (Q-13 改版) 标识。
- `_shared/WORKFLOW.md`：dispatch 时回填 sub_session_id 字段（Q-13a 落地执行点）。

---

## F. sub-agent 写 plan 时怎么用本文件

1. **先读 A.0 + A.1 + A.2** raw 用户原话。
2. **再读 B-1 ~ B-5** 整理后清晰需求。
3. **PLAN 的 acceptance criteria 应该覆盖 B-1 ~ B-5 全部 17 项**（Q-1..Q-13 含 Q-13a/b/c）。
4. **PLAN 的 risks 段应该明示 C-1 ~ C-7**。
5. **PLAN 的 file scope 应该遵循 D 表**（Q-N → SKILL_CORE.md 章节 + Q-13 加 MODEL_ROUTING.md）。
6. **PLAN 的新增 E 节** 要展开 §0.6.2 / §0.7.2 / §0.10.7 / §0.10.8 / MODEL_ROUTING.md / WORKFLOW.md 的细节。
7. sub-agent 发现未澄清 → 写 structured report `AMBIGUITY_RAISED: <问题>`，主编排代问 (Q-6 case B)。

---

## G. 沉淀规约

- 沉淀目录: `G:\ai-toolkit\docs\auto-dev\2026-07-10-skill-meta-flow-control-rules-extended\`
- 流程产物 (按 §4.A 沉淀目录定义):
  - `PLAN.md`（planner 写）
  - `plan.meta.json`（planner 写）
  - `DEFERRED_CODEX_REVIEW.md`（已写，Q-1 fallback 证据）
  - `USER_NEEDS_DIGEST.md`（本文件，主编排 Write，加 Q-13 节完毕）
  - `TEST_TARGET.md`（tester 写，TDD 头）
  - `IMPLEMENTATION_REPORT.md`（developer 写；末尾含 token 报告段 Q-13c）
  - `CODE_REVIEW.md`（code reviewer 写）
  - `TEST_REPORT.md` + `TEST_REPORT.summary.md`（tester 写）
  - `NEXT_ACTIONS.md`（主编排 Write，新批 backlog）
  - **新增**: `TOKEN_USAGE.md`（Q-13c，批后报 token，可由 IMPLEMENTATION_REPORT 内嵌代替）
- 命名规则 (Q-11): 长而清，禁缩；task_id + category + 沉淀目录名 全适用。

---

## H. 本文有效期

- 仅服务于当前 pipeline `skill-meta-flow-control-rules-extended-2026-07-10`。
- 本批 ACCEPTANCE 后，本文归档到 `.ai-work/runs/skill-meta-flow-control-rules-extended-2026-07-10/USER_NEEDS_DIGEST.md`。
- 不修改/不删除，作为下一批（Q-14+）的原始输入溯源材料。
