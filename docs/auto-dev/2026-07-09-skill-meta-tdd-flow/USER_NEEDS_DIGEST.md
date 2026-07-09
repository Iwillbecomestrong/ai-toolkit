# USER_NEEDS_DIGEST.md — 当前 skill meta 改造 pipeline 的用户原始需求 + 整理后版本

> 这是流程产物。主编排写,给下批 planner / developer / tester / reviewer sub-agent 提供 raw + digest 视角。
> 
> **目的**: 让 sub-agent 在写 PLAN 之前先看 user_raw(口述原话)+ user_digest(主编排整理后的清晰需求)两类信息,避免误解;同时也是 § 0.Q-6 "主编排早期提醒 + 整理用户话" 的实施痕迹。

---

## A. 用户原始 raw (最近几轮原话摘录)

### R-1: "你专心改 skill.你都没有启动计划"
- 触发: 主编排之前 partial 改了 SKILL_CORE.md / auto_dev_guard.py / dispatch.ps1 等十几个 skill src 文件, **没派 sub-agent 走 TDD+reviewer 流程** 就直接 Edit。
- 用户纠正: **改 skill 也要走流程**。

### R-2: "但是第一轮要让 deepseekV4pro 做计划呀.然后让 codex 审查呀"
- 用户期待: Tier1 PLAN = deepseek-planner 起步, Codex 异构审 PLAN (出 plan 方 ≠ 审查方)。
- 用户提过我之前没确认这一点, 担心编排层把 Codex 用作 planner(应该不是)。

### R-3: "子代理都在后台跑,然后主编排的对话框不能被阻塞"
- 用户纠正: **主编排派完 sub-agent 应该立即释放**, 不要在 turn 内 block-poll。
- 我之前草拟 §0.8 用 `TaskOutput(block=true, timeout=60s)` 是反模式, 改用 "派 → echo → 等用户消息时回报"。

### R-4: "都需要加上心跳.主编排可以强行让流水线回到计划.还是决定让他们上一批需求跑完,不相关的需求可以新开一个流水线或者如果相关的需求也可以等上一批需求跑完再跑下一批需求,知道所有需求都得到满足"
- 用户需求结构:
  - 4 个 operator: REQUEUE / ABORT_TO_PLAN / PARALLEL_NEW_PIPELINE / CHAIN_AFTER (§0.10)
  - 心跳: sub-agent 60s 回报 (§0.9)
  - 全 AC 满足才算完成 (AC_TRACKER)

### R-5: "让某一条流水线回到计划环节.也可以决定让他们上一批需求跑完,不相关的需求可以新开一个流水线或者如果相关的需求也可以等上一批需求跑完再跑下一批需求,直到所有需求都得到满足"
- 同 R-4 的细化, 强化"先做完再做"语义。

### R-6: "他这个派的名字也是错的.你 plan 都还没派."
- 用户看到 worker 派错 sub-agent (`auto-dev-tester` legacy name) + 跳 planner 出 PLAN 直接 IMPLEMENT/REVIEW。
- 用户期待: 派 `[tester:minimax]` (新 frontmatter) + 先派 planner 出 PLAN。

### R-7: "如果用户插话的话.如果是需求和上一批进去的需求相违背,你就要直接打断了,或者用户就会喊你打断.你最好是能自动判断,那就暂时不跑的需求可能要写在一个地方那里去或者如果和前面那个需求不相关的话,可以新开一个流水线直接跑新一批的需求.这个也要加入到 skill 里去"
- 新需求: **主编排自动判定** user 插话 →
  - 相违背 → 立即打断当前 (用 SendMessage `ABORT_TO_PLAN`)
  - 不相关 → 新开 pipeline (PARALLEL_NEW_PIPELINE)
  - 暂时不跑 → 写到 NEXT_ACTIONS.md 排队 (REQUEUE)

### R-8: "任何 skill 系统层文件修改都必须走 deepseek-planner → Codex/deepseek-reviewer 审查 → developer 补完 → tester 验 → commit 的流程,主编排不能亲自 Edit skill 系统层。如果用了我们的那两个 skill 是要走这样的逻辑的。你只能分配任务给相应的流水线决定流水线的一个状态,没权利直接改动核心部分的东西.核心部分都需要最少经过计划(一般还要计划审查一系列流程)的才能改这种对于修改计划是skills项目来的说是不能让主编排亲自修改的,主编排只能修改一些无关紧要的状态文件和保证流程完成运行你又错了"
- **核心规则**: 主编排不许 Edit skill 系统层文件。只能改 state 文件 + 保证流程完成运行。
- 我之前违反多次 (§0 / §0.5 / §0.6 / §0.7 / §0.8 / §0.9 / §0.10 都亲自 Edit), 已承认。

### R-9: "codex 卡死的话就不要审核了下次就直接测试员先写测试案例"
- 新规则: Codex 卡死 → DEFERRED → **跳过 PLAN_REVIEW 阶段 → 直接派 `[tester:minimax]` 写 TEST_TARGET.md (TDD 头)**。

### R-10: "如果 codex 没额度第二次做计划还是 deepseekV4pro 也是和第一次一样,有额度的话第二次就是 codex 做计划,deepseekV4pro 审核"
- 返工周期分情况:
  - Codex 有额度 → Tier2 角色翻转 (出 plan = Codex xhigh, 审 plan = deepseek-reviewer max)
  - Codex 不可用 → 同第一次 (defer + tester first)

### R-11: "如果有额度了" (前面一条链) + "现在有额度了"
- 用户宽松信号: Codex 现在额度可用。
- 我立即派 Codex Tier1 异构审 PLAN (bg 跑)。但 Codex CLI exit -1 又卡了。

### R-12: "你这些需求可以用一个小本本记下来.如果不新开流水线的话,建议是等上一批需求搞完再做这批需求的计划"
- 用户指示: 多余/排队需求写到一个小本本(`NEXT_ACTIONS.md`),不开新 pipeline, 等当前 pipeline 跑完再 plan。

### R-13: "用户有些需求不明确或有错误的时候你这个主编排要在计划早期提醒用户,明显有问题的时候,你要今早告诉用户,如果你没发现在后续的子代理发现了,你也要代替你的子代理询问用户提醒用户.你记得可以整理一下用户的话,更方便子代理写 plan"
- **新规则**: 主编排
  - 早期发现用户需求不明确 / 错误 → 主动提醒 (plan 派发前)
  - 后续 sub-agent 发现问题 → 主编排代 sub-agent 询问用户
  - 整理用户的话 → digest 给 sub-agent 写 plan 用

### R-14: "如果用户插话的话..."
- 同 R-7

### R-15: "他这个派的名字也是错的.你 plan 都还没派."
- 同 R-6

---

## B. 主编排 digest (整理后)

### B-1. 核心 meta 规则 (强)
1. **改 skill 系统层必须走 deepseek-planner → reviewer → developer → tester → reviewer(diff)→ commit 流程**。主编排不许 Edit skill src (R-8)。编辑对象只允许:
   - 沉淀文件 (`docs/<skill>/<date-task>/`)
   - state 文件 (`AGENT_REGISTRY.json`, `PLAN_REVIEW.md`, `TEST_TARGET.md`, `NEXT_ACTIONS.md`, `DEFERRED_CODEX_REVIEW.md`)
   - HANDOFF.md / diff.patch / IMPLEMENTATION_REPORT.md 等流程产物

2. **异构底线**: 出 plan 方 ≠ 审 plan 方, 永远。Codex 不可用时 **DEFERRED**, 不得降级 deepseek 代替 Codex (R-9)。

3. **流程顺序 (§0.6.4)**: DEVELOP → TEST → REVIEW → ACCEPTANCE 严格串行, 不可并行 tester + reviewer。

4. **返工周期分情况 (R-10)**:
   - Codex 有额度 → Tier2 (Codex 出 plan xhigh, deepseek 审 max)
   - Codex 不可用 → 沿用 Tier1 (deepseek 出 plan + DEFERRED + tester first)

### B-2. 控制面 4+2 个 operator (§0.10)
1. `REQUEUE` — 写到 NEXT_ACTIONS.md 排队 (R-12)
2. `ABORT_TO_PLAN` — 用 SendMessage 让 in-flight sub-agent 停手 → planner 出 PLAN_PATCH
3. `PARALLEL_NEW_PIPELINE` — 新开 pipeline (新目录,新 task_id)
4. `CHAIN_AFTER` — 等当前 pipeline 完成 → 下一批需求
5. `INTERRUPT_AND_RE_PLAN` (Q-5 新加) — user 插话 contradiction 时立即 ABORT_TO_PLAN
6. `DETECT_CONTRADICTION` (Q-5 新加) — 主编排自动判定新需求与 in-flight plan 的关系

### B-3. 主编排基础 prompt (新增)
- **早期发现 user 需求不明确 / 错误** (R-13) — plan 派发前主动问
- **sub-agent 发现问题时 主编排代问** (R-13)
- **整理 user 的话 → digest** (R-13) — 本文件就是实现样本
- **sub-agent 跑 background, 主 session 不阻塞** (R-3)
- **每个 sub-agent 派单调必须显示 model + effort** (既有的 Gate 7, 已写)

### B-4. 当前 pipeline 状态 (skill meta 改造)
- ✅ PLAN 已出 (deepseek-planner)
- ⚠ PLAN_REVIEW DEFERRED_due_to_codex_unavailable (Codex CLI exit -1,真 Codex 卡死)
- ⏳ TEST_TARGET.md 正在写 (general-purpose 替身, bg 跑 task-id `aa90fab008cddd5ae`)
- ⏳ developer 接力 (TBD)
- ⏳ tester 跑
- ⏳ Codex Tier1 异构审 diff (无 Codex → deepseek-reviewer fallback)

### B-5. 当前 pipeline 完成后的下一批 (NEXT_ACTIONS.md 已记)
- Q-1 Codex 卡死 → DEFERRED + tester first 规则 (已写)
- Q-2 返工周期分情况 (已写)
- Q-3 PLAN_REVIEW 三态枚举 (已写)
- Q-4 异构性自纠错 (已写)
- Q-5 用户插话 自动判定 4+2 operator (已写)
- Q-6 早期发现 user 需求不明确 + sub-agent 代问 (本文件记)

这些 Q 由 developer 接力 commit 时一并写入 SKILL_CORE §0.7 / §0.10 / §0.11(新)。

---

## C. 用户可能的"未澄清"或"自相矛盾" 已经识别 (供下批 planner 留意)

### C-1. "Codex 现在有额度了" 不稳定
- 用户多次说"现在有额度"但 Codex CLI exit -1。可能 Codex server-side 通病 / 当前 API endpoint 不稳。
- 下次规划时, sub-agent 应该跑 MODEL_QUOTA_CHECK.md.template 那套指令 check, 不要纯用户口头说"额度有" 就直接跑。

### C-2. "用我们的那两个 skill" 指什么?
- 用户提到"我们的那两个 skill",但当前能看到的有 auto-dev, auto-code-android-dev 等多个 skill。可能指两个 user 主要用的 (auto-dev + auto-code-android-dev)。
- 下次 plan agent 应该 cat `~/.claude/skills/` 和 `~/.agents/skills/` 列表确认。

### C-3. "AI 前置过滤脚本" 模糊
- IronWill 那批日志系统改造有 `filter_ai_log.ps1`,但用户前后没明说"AI" 是模型还是别的。sub-agent 自己推断可能不对。
- 下次 plan agent 应该确认 "AI" 指什么 — 是 LLM 过滤? 是 AI 公司(Anthropic 公司)的工具? 还是 OpenAI Codex?

### C-4. "skill src 第一轮要 deepseekV4pro 做计划, 然后 codex 审查" — 何时升级到 Tier2
- 用户讲了"返工时分情况", 但首次出 PLAN 时 Tier1 永远 deepseek + Codex? 用户没明说"首次也分 Codex 可用情况"。
- 但隐含逻辑: 首次 PLAN 也要分级 — Codex 卡死就 DEFERRED + tester first。

### C-5. "没改好" / "没改完" 是什么状态
- 用户多轮用 "依旧 / 还是 / 没改好", 这些都走 UserPromptSubmit hook bug-report → 回 planning。但 sub-agent dispatch 与 hook 是不同时, hook 是不是覆盖 sub-agent context 不明。
- 下次 plan 应该让 planner hook 跑一次看效果。

---

## D. sub-agent 写 plan 时怎么用本文件

1. 先读 `R-1 ~ R-15` raw 用户的原话,理解情绪 + 语气 + 隐含语义。
2. 再读 `B-1 ~ B-5` digest,理解主编排整理后的清晰版本。
3. 写 PLAN 时 acceptance criteria 应该覆盖 `B-1 ~ B-3` 列出的所有规则 (不是仅字面需求)。
4. 写 PLAN 时 risks 段应该明示 `C-1 ~ C-5` 这些"未澄清 / 自相矛盾"项,作为 unknowns。
5. 写 PLAN 后应该 developer 接力修复 (本批已知 bug 见 B-4: model=minimax 错 id 等)。

---

## E. 本文有效期

- 仅服务于当前 skill meta 改造 pipeline (skill-meta-tdd-flow-2026-07-09)。
- 当本 pipeline ACCEPTANCE 后,本文归档到 `.ai-work/runs/skill-meta-tdd-flow-2026-07-09/USER_NEEDS_DIGEST.md`(如果 ACTIVE pipeline 改用 .ai-work/runs/)。当前位置在 docs/auto-dev/.../ 沉淀目录,是 SKILL_CORE §4.A 项目侧沉淀 (非 skill src)。
- 不修改/不删除,作为下一批 Q-1~Q-6 的原始输入溯源材料。
