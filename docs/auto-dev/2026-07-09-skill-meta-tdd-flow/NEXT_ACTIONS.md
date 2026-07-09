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
- **判定算法 (主编排当下 turn self-check, file-overlap 聚类)**:
  - 用户最新纠错:"两两比较复杂度还挺高的吧。应该是看修改需求主要改哪几个文件,有交集放一类,没交集放一类"
  - 正确算法 (Q-12 单独列出细节, 这里是简版):
    1. 列出每个 Q 的 `files_to_modify` 集合 (主 skill src 文件 — SKILL_CORE.md / auto_dev_guard.py / dispatch.ps1 / claude-*.md / hooks.claude.json / templates / scripts)
    2. 计算两 Q 的 file overlap: `|files(Q_i) ∩ files(Q_j)|` > 0 → 同 cluster; = 0 → 不同 cluster
    3. cluster 内可串行, cluster 间可并行
    4. **不做 pairwise 相似度排序** — 只看 file 重叠(集合论,O(N) 不是 O(N²))
  - **何时跑**: **聚类是个**优化, **不是必须**。 "在做计划之前都可以偶尔来聚个类,有时间的话" — 主编排有闲 + 没 bg 任务时(Q-10 idle)顺手跑, 不强制, 不阻塞流水线
  - **触发条件**: backlog ≥ 3 个 Q 时聚类最划算; < 3 直接 `CHAIN_AFTER` 一锅端
  - 跟"耦合度高=CHAIN_AFTER / 低=PARALLEL_NEW_PIPELINE" 一致, 但用 file overlap 而不是人工判断
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

- **严禁等 plan agent 反过来告诉主编排 "需求不明确"** — 主编排当下 turn 就判定(Q-6)
- **严禁主编排自己 Edit SKILL_CORE.md 提前把 Q-N 规则写进 src** (违背 user 的 "主编排不许 Edit skill 系统层")
- 严禁任何 sub-agent 直接 call user prompt;只能通过 structured report `AMBIGUITY_RAISED` 字段汇报 + 主编排代问 (Q-6 case B)
- 严禁 sub-agent 后台跑阻塞主 session;主 session 不阻塞是默认(Q-8 续)

### Q-8. 流水线并行 / 串行柔性化规则 (用户最新纠错)
- **user 最新指示**: "严禁把 Q-1~Q-7 立即开新 pipeline 并行跑" 这些又太绝对了,应该是耦合度很高的需求建议串行,偶尔都不高的话可以并行,如果需求很多可以根据需求分类每一类并行跑的。每三个需求最多可以开一个流水线。"
- **正确处理 (柔性, 不是死规则)**:
  - 默认 `CHAIN_AFTER` (串行)— 单一需求追加到当前 pipeline
  - 同一 pipeline 内部: 串行 (ac → ac 顺序, 测试先行不可并行)
  - 跨 pipeline: **耦合度判** —
    - 高耦合 (改同一文件 / 同一 state / 同一接口): CHAIN_AFTER (等上一批跑完)
    - 低耦合 (不同模块 / 不同 state / 不同文件): `PARALLEL_NEW_PIPELINE` (新 task_id + 新 .ai-work/runs/)
  - **每三个需求最多开一个 pipeline** = 需求多按耦合度分类, 每类一个 pipeline (上限)
  - 需求极少 (1-2 条且耦合): 一个 pipeline
  - 需求多 (≥3 条) 耦合度异质: **按耦合度分 pipeline**(不是禁止并行,而是按需并行)
- **判定算法 (主编排当下 turn self-check)**:
  1. 列出当前 backlog Q-N
  2. 两两比对耦合度:候选一对 Q 改同一文件 / 同一 state / 同一接口 → 高耦合; 改不同模块 → 低耦合
  3. 按耦合度聚类:把 backlog 拆成 K 个 cluster (每个 cluster ≤ 3 个 Q); K 个 pipeline 各自串行
  4. 都耦合就一个 pipeline (CHAIN_AFTER)
- **反模式 (本次纠错)**: 严禁 "一刀切" — 不论耦合度都禁止并行 / 不论耦合度都允许并行, 都错。 看耦合度而定。
- **哪里落地**: `_shared/SKILL_CORE.md` §0.9 + §0.10 改写柔性版
- **哪些 sub-agent 接力**: developer

### Q-9. 主编排疏漏接受 + 子代理不阻塞主 session
- **user 最新指示**: "主编排也难免有疏漏你也很难保证主编排就完全没错,这也是可以的,最好好主编排前期就把需求确定好。如果子代理发现有问题还是可以给主编排汇报的。子代理一般跑在后台不要阻止主编排接受用户实时的需求"
- **正确处理 (修订 §0.6 + §0.8 + Q-6)**:
  - 主编排也难免疏漏 (这是允许的, 不要追求 100% 完美) — 但应该:
    - 前期把需求确定好 (用 `USER_NEEDS_DIGEST.md` + 当下追问)
    - 主编排疏漏被用户 / sub-agent 提醒时,**承认并立即修正** (Q-6 case A 是当下主动问; 但若疏漏被 user 警告, 直接认错 + 立即修正)
  - sub-agent 发现 ambiguity 仍通过 `AMBIGUITY_RAISED` 给主编排汇报 (Q-6 case B 已经写了, 这里强化)
  - **子代理后台跑不阻止主编排接受用户实时需求** — 主 session 永远 receptive (§0.8 已写):
    - 主编排不能"在 bg sub-agent 完成前独占 turn"
    - 主 session 收到新 user message 必须能立即响应, 不能因 bg 任务 ongoing 而排队等
    - 这是 §0.8 主 session 不阻塞规则的强化版
- **哪里落地**: `_shared/SKILL_CORE.md` §0.8 + §0.6.1 + §0.11 加 "疏漏接受 + always receptive" 段
- **哪些 sub-agent 接力**: developer

### Q-10. 主编排 idle 时主动 classifier
- **user 指示**: "子代理在后台跑主编排没事干的时候可以对查看文件,了解需求并进行分类。子代理有结果再回来处理一下,如果用户有问题也可以回答一下。有需求就接下需求"
- **正确处理** (主 session 永远 receptive 子集 — 主动而不是被动):
  - 在 bg sub-agent 跑时,**主编排 idle 不阻塞**用户消息 — 但**主动**:
    - `cat` / `grep` / `glob` 当前 active pipeline 的 `STATE.json` / `IMPL_REPORT.md` / `TEST_REPORT.md` / `PLAN.md` 看进展
    - `ls` `docs/<skill>/<date-task>/` 沉淀目录, 了解历史 + 沉淀状态
    - `grep NEXT_ACTIONS.md` 看 Q backlog 总览, 给用户更准 backlog view
    - 检查 `.codex-runtime/` 子目录 + `CURRENT_CODEX_RUN.json` + `AGENT_REGISTRY.json` 健康度
  - 收到 bg sub-agent 结果后立即"捡起" 处理(grep `AMBIGUITY_RAISED`, echo 追问, dispatch 下一阶段)
  - 收到 user 问题立即回答(不停等 bg)
  - 收到 user 新需求立即按 Q-5/Q-6 + Q-8 处理(当下 turn self-check)
- **不能做的事** (Q-6 / R-8 约束):
  - 不能 Edit skill 系统层文件 (SKILL_CORE.md / auto_dev_guard.py / dispatch.ps1 / claude-{developer,tester,researcher}.md 等)
  - 不能 Edit 已 spawn 的 bg sub-agent 正在写的文件(避免 race)
  - 不能 Write/Edit `NEXT_ACTIONS.md` 之外的"已 commit pipeline 文件" (commit_step_gate)
- **落地**: `_shared/SKILL_CORE.md` §0.8 强化 + §0.11 加 "idle-time classifier" 段
- **哪些 sub-agent 接力**: developer

### Q-11. 命名规则 —— 主要针对 category name + 长而清楚,全词或中文
- **user 指示**: "名字最好是起长一点,方便辨别,不要还有字母理解成本,一般采用几个英文单词全程或者中文。类别名称的名字"
- **核心**: 派单对象 (Category / sub-pipeline / dispatch label) **看名字立即知道派给谁、改什么**:
  - 字母理解成本 = 0 (人读到名字立即明白含义)
  - 几个英文单词全程 或 中文;**禁用** `skill-meta` / `pipeline-fg` / `pipeline-logging` 这种缩
  - 不创造新缩写 — 用既有的全词拼接
- **主要对象 — `category name` / `category_id`** (categories.md 里的类别,贯穿整个 pipeline):
  - ❌ `category-fg-bypass` ("fg" + "bypass" 不明)
  - ❌ `category-dnd-locked` ("dnd" 缩)
  - ❌ `skill-meta` ("meta" 缩)
  - ✅ `category-foreground-bypass-and-foreground-app-detection-rule` (长,清)
  - ✅ `category-dnd-time-window-and-locked-app-policy-rule` (长,清)
  - ✅ `category-ironwill-foreground-app-detection-and-unlock-coverage-test-suite`
  - ✅ `category-skill-meta-tdd-and-flow-control-rules-synthesis`
- **次要对象** (也适用):pipeline name / task id / docs/<skill>/<date-task>/ 子目录 / run id / agent template 描述
- **例外** (不可改的内置名):
  - Claude Code built-in agent types: `general-purpose` / `Explore` / `Plan` / `statusline-setup`
  - Codex runner `-Action`: `codex-plan` / `codex-review` / `codex-implement`
  - 终端 display: `[planner:deepseekV4pro]` / `[developer:minimax]` 等
- **本任务已 commit 不回改**:
  - 当前 docs 目录 `2026-07-09-skill-meta-tdd-flow/` 已 commit, 不强行回改(回改会破坏 git history)
  - 但下一批 Q-1~Q-9 启动新 pipeline 时**严格**遵守新规则
- **落地**: `_shared/SKILL_CORE.md` §0.11 加 "命名规则段"; `_shared/SKILL.md` + `WORKFLOW.md` 引用
- **哪些 sub-agent 接力**: developer

## 当前 pipeline 跑完后做的事 (修订后)

按 §0.8 + §0.9 + Q-8(柔性化)规范,这些 Q-1~Q-9 在当前 pipeline 完成 (ACCEPTANCE) 后,**先按耦合度聚类**:

1. 当前 pipeline `6. ACCEPTANCE` 完成时,主编排读 `IMPLEMENTATION_REPORT.md` 决定 "全部 AC 满足"
2. 列出 backlog Q-1~Q-9,两两比对耦合度
3. K 个 cluster,每 cluster 一个 pipeline (上限 3 个 Q/pipeline):
   - **示例 cluster A (skill core rules)**: Q-1(Q-7/B1/Q-6/Q-9 都改 SKILL_CORE.md / 改 sub-agent protocol / 改 dispatch.ps1) → 高耦合 → 同 pipeline
   - **示例 cluster B (流水线编排规则)**: Q-5 / Q-8 / Q-9 多半涉及 SKILL_CORE / 编排 / 队列, **与 cluster A 部分耦合**;若按文件看是同 SKILL_CORE,那也同 pipeline
   - **示例 cluster C (独立可拆)**: 若有"换 dispatcher 路径"或"换 agent backend" 这类需求 → 不同模块 → 新 pipeline
4. 每个 cluster 派 `[planner:deepseekV4pro]` 出 PLAN + 完整 TDD+reviewer 流程
5. cluster 间可并行 (低耦合, 不共享文件)
6. 把当前 PLAN_REVIEW.md + NEXT_ACTIONS.md + USER_NEEDS_DIGEST.md 合并入下一批 PLAN 的 reference
