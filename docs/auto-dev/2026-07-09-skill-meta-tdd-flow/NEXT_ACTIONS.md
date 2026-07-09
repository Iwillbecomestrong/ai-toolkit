# NEXT_ACTIONS.md — 当前 skill meta 改造 pipeline 排队的需求

> 这是流程产物 (docs/auto-dev/<date-task>/NEXT_ACTIONS.md),不是 skill 系统层。
> 主编排可以 Write。这里 **不开新 pipeline**,排队到当前 pipeline 跑完一起处理。

## 排队需求 (Q-N)

### Q-1. Codex 卡死 → DEFERRED → 跳过 PLAN_REVIEW → tester first
- **触发场景**: Codex CLI 卡死 (exit -1) 或 无额度
- **当前问题**: 我 (主编排) 之前下意识 "降级" 到 deepseek-reviewer, **丧失异构底线**
- **正确处理**:
  1. 写 `runs/<pipeline-id>/DEFERRED_CODEX_REVIEW.md` 标 `reviewer_status = deferred_due_to_codex_unavailable`
  2. **不解锁 developer**,直接派 `[tester:minimax]` (model=minimax, effort=medium) 写 TEST_TARGET.md (TDD 头)
  3. tester 完成后 → developer → tester 跑测试 → reviewer (异构底线对 code review 工位宽松,codex / deepseek-reviewer 都可以) → ACCEPTANCE
- **哪里落地**: `_shared/SKILL_CORE.md` §0.7 加一段 "Codex 卡死 / DEFERRED handling"
- **哪些 sub-agent 接力**: developer (`[developer:minimax]`) 在 atomic commit SKILL_CORE 时一并写入

### Q-2. 返工周期 (PLAN_PATCH) 分情况策略
- **触发场景**: 第一轮 PLAN 出 `REQUEST_CHANGES`,planner 修订出 PLAN_PATCH.md,进入第二轮
- **正确处理 (按 Codex 状态分)**:
  - Codex **有额度**: 返工出 plan = `Codex gpt-5.5 xhigh` (Tier2 角色翻转) + 审 plan = `deepseek-reviewer fable max` (异构)
  - Codex **不可用**: 返工出 plan = `deepseek-planner fable max` (沿用第一次) + **DEFERRED + skip + tester first** (跟第一次 Codex 卡死时一样处理)
- **哪里落地**: `_shared/SKILL_CORE.md` §0.7 返工周期那张表改成表格 (有/没 额度 两行)
- **哪些 sub-agent 接力**: developer 在 atomic commit SKILL_CORE 时一并写入

### Q-3. PLAN_REVIEW 阶段三态枚举
- **触发场景**: 明确合法结局
- **正确处理**: PLAN_REVIEW 阶段只有三个合法结局,任何其它状态都视为异常路径:
  - `APPROVE` → 进入 developer
  - `REQUEST_CHANGES` → 回 planner 修订,再走一轮 §0.7
  - `DEFERRED_due_to_codex_unavailable` → skip PLAN_REVIEW → tester first (走 Q-1 路径)
- **哪里落地**: `_shared/SKILL_CORE.md` §0.7 注释三态枚举
- **哪些 sub-agent 接力**: developer

### Q-4. 主编排 "同源审 同源" 自纠错
- **触发场景**: 这次实际发生 — 我 (主编排) 让 `deepseek-reviewer` 审 `deepseek-planner` 出的 PLAN, **丧失异构性**,作废
- **正确处理**: 主编排如发现 CODE 已无异构性,**必须回滚**,重新派真异构 reviewer (Codex) 或按 DEFERRED + skip 路径走
- **哪里落地**: `_shared/SKILL_CORE.md` §0.6.2 reviewer 必派硬规则 加一条 "异构性自纠错"
- **哪些 sub-agent 接力**: developer

### Q-5. 用户插话自动判定 (CONTRADICTION / UNRELATED / DEFERRED)
- **触发场景**: 用户在 sub-agent bg 跑时插一条新需求
- **正确处理**: 主编排**立即**(收到 user message **当下 turn**, 在派任何 sub-agent 之前 — **不能等 plan 阶段**)判定新需求与当前 pipeline / 当前 PLAN 的关系:
  - 需求 **不明确 / 错误 / 含糊** → 立即 echo 追问,**不派任何 sub-agent**
  - `CONTRADICTION` — 新需求与当前 PLAN 或 in-flight 实现相违背 → 立即用 `SendMessage` 给当前 background sub-agent 发 "stop, 回 planner 拿新 plan。先 echo 当前进度 + 状态", 然后 `ABORT_TO_PLAN` 让 planner 出 `PLAN_PATCH`
  - `UNRELATED` — 新需求与当前 pipeline 完全没有依赖关系 (不同模块/不同文件/不同 state) → `PARALLEL_NEW_PIPELINE` (新 task-id,新 .ai-work/runs/ 目录,新 docs/<skill>/<date-task>/)
  - `DEFERRED` — 新需求不紧急 / 等上批跑完再做 → 写到 `NEXT_ACTIONS.md` (当前 pipeline 目录) 不开新 pipeline
- **判定算法 (主编排当下 turn self-check)**:
  1. 读 user message + 当前 active pipeline 的 `PLAN.md` 与 in-flight sub-agent 的 prompt
  2. 读新需求的 phrases,搜关键词 vs 当前 PLAN 的 acceptance criteria / candidate files
  3. 命中"相同文件/相同 state/逆向行为 (e.g. 这次允许 sonnet 下次拒)" → `CONTRADICTION`
  4. 无共享关键词 + 不同模块 → `UNRELATED`
  5. 用户显式说"先记下 / Q3 再说 / 等 X 完" → `DEFERRED`
  6. **含糊 / 关键词不命中 / 多种合理解释 → 不派 sub-agent, 立即 echo 追问**
- **哪里落地**: `_shared/SKILL_CORE.md` §0.10 加 ⑤ (INTERRUPT_AND_RE_PLAN) + ⑥ (DETECT_CONTRADICTION) + §0.11 加 "主编排当下判定时机"段
- **哪些 sub-agent 接力**: developer

### Q-6. 主编排当下判定时机 + sub-agent 发现 ambiguity 也代问
- **user 两条指示合并**:
  - R-13a: "应该是主编排的时候就要判断了,不是在计划早期"
  - R-13b: "如果主编排没发现而是后面的子代理发现了,主编排同样是帮忙询问一下用户"
- **核心**: 主编排收到 user message 后,**当前 turn 内**(在派任何 sub-agent / Bash / Write 之前)就完成判定:
  - 需求 **不明确 / 错误** → echo 追问,**不派任何 sub-agent**(case A 主编排自行判定)
  - sub-agent 跑过程中发现 ambiguity/error → sub-agent **不能直接 call user**(sub-agent 没 user-facing 通道),在 structured report 加 `AMBIGUITY_RAISED: <问题>` 字段,主编排**代为**问用户(case B 主编排代 sub-agent 问)
  - 两条路径都禁止 sub-agent 直接调 user prompt;只能让主编排集中汇总 + echo 一次
- **sub-agent protocol 强化**:
  - sub-agent 不允许直接 call AskUserQuestion 或类似工具;必须通过 structured report `AMBIGUITY_RAISED` 字段回报
  - 主编排在 sub-agent 返回后立刻 grep `AMBIGUITY_RAISED`,有的话**当下 turn** echo 追问用户(case B)
- **反模式 (本次纠错)**: 不要等 plan agent / sub-agent 反馈 "plan 写不出来因为需求不明确"。 主编排先问。也不要让 sub-agent 自己直接调 user。
- **哪里落地**: `_shared/SKILL_CORE.md` §0.11 "主编排当下判定时机" 段
- **哪些 sub-agent 接力**: developer

### Q-7. 整理用户话给 sub-agent 写 plan (USER_NEEDS_DIGEST.md 风格)
- **user 指示**: "可以整理一下用户的话,更方便子代理写 plan"
- **正确处理**: 主编排收到 user message 后,写/append `USER_NEEDS_DIGEST.md` 同时含 raw(口述原话)+ digest(整理后版本)+ 已知未澄清 (让 sub-agent 写 plan 时留意)
- **落地**: `docs/<skill>/<date-task>/USER_NEEDS_DIGEST.md` 与 PLAN.md 同目录
- **sub-agent 用法**: 先读 `USER_NEEDS_DIGEST.md` raw + digest,再写 PLAN,Plan risks 段应该包含 "未澄清项"
- **哪里落地**: `_shared/SKILL_CORE.md` §0.11 "用户 digest 段"
- **哪些 sub-agent 接力**: developer

## 当前 pipeline 跑完后做的事

按 §0.9 CHAIN_AFTER 规范,这些 Q-1~Q-7 在 skill meta 改造 pipeline 完成 (ACCEPTANCE) 后,**跟下一批需求一起 plan**。具体时机:

1. 当前 pipeline `6. ACCEPTANCE` 完成时,主编排读 `IMPLEMENTATION_REPORT.md` + Codex final review 决定是否 "全部 AC 满足"
2. 若满足 → 全 AC 关闭,用户验收
3. 启动下一批 (这批 Q-1~Q-7) 时:
   - 派 `[planner:deepseekV4pro]` (Tier1 since plan 总用 deepseek 起步) 出 PLAN_for_Q1toQ7.md
   - 先读 `USER_NEEDS_DIGEST.md`(已记 — R-1 ~ R-15 + digest)
   - (try Codex first; 不可用 → DEFERRED + tester first)
   - developer 落地
   - tester 验
   - reviewer (codex if available / deepseek-reviewer fallback)
4. 把当前 PLAN_REVIEW.md + NEXT_ACTIONS.md + USER_NEEDS_DIGEST.md 合并入下一批 PLAN 的 reference

## 严禁

- 严禁把 Q-1~Q-7 立即开新 pipeline 并行跑(违背 §0.9 串行)
- 严禁因为 "等不及" 跳过 CURRENT 流程去处理 Q-1~Q-7(违背 §0.6.4 流程顺序)
- 严禁主编排自己 Edit SKILL_CORE.md 提前把 Q-1~Q-7 的规则写进 src(违背 user 的 "主编排不许 Edit skill 系统层")
- **严禁等 plan agent 反过来告诉主编排 "需求不明确"** — 主编排当下 turn 就判定
