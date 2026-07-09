# PLAN.md — skill-meta-flow-control-rules-extended-2026-07-10

## 1. 需求复述与验收标准

为 backlog Q-1 ~ Q-13（含 Q-13a/Q-13b/Q-13c）生成扩版实施计划，后续落地目标是把流程控制、模型路由、session 复用、token 报告、用户插话判定、命名规则和 file-overlap 聚类规则同步写入 auto-dev 共享规则层。

目标产物路径：

- `G:\ai-toolkit\docs\auto-dev\2026-07-10-skill-meta-flow-control-rules-extended\PLAN.md`
- `G:\ai-toolkit\docs\auto-dev\2026-07-10-skill-meta-flow-control-rules-extended\plan.meta.json`

本角色只读，不直接写文件。

验收标准 AC-1 ~ AC-17：

1. Q-1：Codex 卡死/超时时，PLAN_REVIEW 进入 `DEFERRED_due_to_codex_unavailable`，写 `DEFERRED_CODEX_REVIEW.md`，走 tester first，不用 DeepSeek 假装替代 Codex 审 plan。
2. Q-2：返工周期表覆盖 Codex 有/无额度、首次/返工、DeepSeek `<500k` 可再来一轮、`>=500k` 需拆新 pipeline。
3. Q-3：PLAN_REVIEW 合法状态只允许 `APPROVE` / `REQUEST_CHANGES` / `DEFERRED_due_to_codex_unavailable`。
4. Q-4：主编排派 reviewer 前必须检查异构性；发现同源自审立即回滚或 DEFERRED。
5. Q-5：用户插话自动判定 4+2 operator，含 `INTERRUPT_AND_RE_PLAN` 与 `DETECT_CONTRADICTION`。
6. Q-6：主编排必须在收到用户消息当下判定 case A；sub-agent 发现歧义走 case B `AMBIGUITY_RAISED`，不得直接问用户。
7. Q-7：`USER_NEEDS_DIGEST.md` 协议写清 raw、digest、unknowns、sub-agent 使用顺序。
8. Q-8：流水线并行/串行柔性化规则写清，同类串行，不同类低耦合才并行。
9. Q-9：主编排疏漏可被用户插话纠正，主 session 不因后台 sub-agent 阻塞。
10. Q-10：idle classifier 明确空闲、等待后台、等待用户、blocked、可推进等状态。
11. Q-11：命名规则长而清，禁缩写，覆盖 task_id/category/pipeline/dispatch label/沉淀目录。
12. Q-12：file overlap 聚类算法写成可执行集合规则，明确共享文件、依赖方向和并行限制。
13. Q-13：Tier1 主路由 swap 为 Codex gpt-5.5 high 出 PLAN、DeepSeek V4 Pro max 审 PLAN、Codex gpt-5.5 high 审 CODE。
14. Q-13a：同一 pipeline 内所有 sub-agent dispatch 回填同一个 `sub_session_id = <pipeline_id>`；Codex CLI 侧映射为 `resume <session_id>` / `-SessionId`。
15. Q-13b：DeepSeek 单轮输入 context `<500k token` 可允许一轮返工；`>=500k` 由主编排判断拆新 pipeline。
16. Q-13c：每批完成后，`IMPLEMENTATION_REPORT.md` 末尾和 ACCEPTANCE 报告必须列 sub-agent session token_usage 明细。
17. Q-13 fallback chain：L0 Codex plan + DeepSeek plan review + Codex code review；L1 Codex 卡死则 DEFERRED + tester first + DeepSeek fallback；L2 Codex/DeepSeek 都卡则 single agent shell default，标 warning 后接受。

## 2. 分类与执行顺序

CAT-0：计划与元数据产物  
先产出 `PLAN.md` 与 `plan.meta.json`，不改源码，不进入实现。

CAT-1：模型路由 swap 与 DEFERRED/fallback  
覆盖 Q-1/Q-2/Q-3/Q-4/Q-13。先改，因为后续所有流程文字都依赖新 Tier1/Tier2 表。

CAT-2：session 复用与 token 阈值/报告  
覆盖 Q-13a/Q-13b/Q-13c。依赖 CAT-1 的模型角色定义。

CAT-3：用户插话、主 session receptive、idle classifier  
覆盖 Q-5/Q-6/Q-7/Q-9/Q-10。依赖 CAT-1 的阶段状态枚举。

CAT-4：并串行与 file overlap 聚类  
覆盖 Q-8/Q-12。依赖 CAT-3 的打断/排队 operator。

CAT-5：命名规则与跨文件同步  
覆盖 Q-11，并把前面新规则同步到入口摘要和 workflow 叙述。最后做，避免旧表残留。

执行顺序：CAT-0 → CAT-1 → CAT-2 → CAT-3 → CAT-4 → CAT-5 → 全量一致性检查。

## 3. 影响模块与候选文件

默认允许修改的候选文件：

- `G:\ai-toolkit\skills\_shared\SKILL_CORE.md`
- `G:\ai-toolkit\skills\_shared\MODEL_ROUTING.md`
- `G:\ai-toolkit\skills\_shared\WORKFLOW.md`
- `G:\ai-toolkit\skills\auto-dev\SKILL.md`

验证只读候选文件：

- `G:\ai-toolkit\skills\_shared\scripts\dispatch.ps1`：已有 `-SessionId` 参数和 `session=...` echo，默认不改。
- `G:\ai-toolkit\skills\_shared\scripts\show_session_context.py`
- `G:\ai-toolkit\skills\_shared\scripts\test_show_session_context.py`
- `G:\ai-toolkit\skills\_shared\scripts\test_auto_dev_guard.py`
- `G:\ai-toolkit\skills\_shared\REPORT_FORMATS.md`

明确不进本批 scope：

- `install-all.ps1`
- `manifest.json`
- nested-submodule-restructure 相关脏文件
- 任意业务源码
- push / merge / release / commit 操作

注意：需求提到的 `skills\_shared\SKILL.md` 当前不存在。计划临时以 `skills\auto-dev\SKILL.md` 作为入口摘要同步候选；是否新建 `_shared\SKILL.md` 见末尾歧义项。

## 4. 实施任务与依赖

1. 产出 CAT-0 文档：写 9-section `PLAN.md`，`plan.meta.json` 标记 `risk_level=HIGH`、`ac_count=17`、`files_in_scope=4`。
2. CAT-1 修改 `SKILL_CORE.md` §0.6.2/§0.7：把旧 “DeepSeek 出 plan → Codex 审 plan” 改为 Q-13 新 Tier1；保留 Q-1 DEFERRED 作为 fallback，而不是删除。
3. CAT-1 同步 `MODEL_ROUTING.md`：默认分工、Tier1/Tier2 表、Planner Rule、effort 说明、fallback chain 全部改成新路由。
4. CAT-2 修改 `SKILL_CORE.md` §0.10 新增 session/token 小节：规定 `sub_session_id=<pipeline_id>`、DeepSeek 500k 阈值、批后 token 报告模板。
5. CAT-2 同步 `WORKFLOW.md`：阶段交接表和 dispatch 协议必须包含 `sub_session_id`，并说明跨 provider 只保证 orchestrator session id 一致，不保证跨 provider cache 命中。
6. CAT-3 修改 `SKILL_CORE.md` §0.8/§0.10/§0.11：补齐插话判定、case A/B、USER_NEEDS_DIGEST、idle classifier、主 session 不阻塞规则。
7. CAT-4 修改 `SKILL_CORE.md` §0.9/§0.10/§0.11：写 file overlap 聚类算法，明确共享文件即同类或串行依赖。
8. CAT-5 修改 `SKILL_CORE.md` §0.11 与 `WORKFLOW.md`/`auto-dev\SKILL.md` 摘要：写长而清命名规则，删除/替换旧缩写示例。
9. 全量一致性扫尾：grep 旧路由、旧模型描述、旧 `GPT-5.4` 第一轮审查描述、旧 “DeepSeek planner Tier1” 残留，逐条修正。
10. 更新实施报告模板要求：确保后续 developer 在 `IMPLEMENTATION_REPORT.md` 末尾加入 token_usage 明细。

## 5. 每类允许修改范围

CAT-0：只允许写 docs 沉淀目录下 `PLAN.md` / `plan.meta.json`。

CAT-1：只允许改模型路由、PLAN_REVIEW 三态、DEFERRED、fallback、异构性检查相关段落；不得改 TDD 基本顺序。

CAT-2：只允许改 session id、token threshold、token report 规则；不得改 `dispatch.ps1`，除非实现阶段发现文档规则无法通过现有 `-SessionId` 表达。

CAT-3：只允许改用户插话、主编排当下判定、后台 sub-agent、USER_NEEDS_DIGEST、idle classifier；不得放宽 tester/reviewer 必派。

CAT-4：只允许改并行/串行、file overlap、pipeline queue、分类算法；不得新增业务 pipeline 常驻分类。

CAT-5：只允许改命名规则和入口摘要同步；不得重命名已归档历史目录。

## 6. 检查与测试覆盖

快速自检：

- `rg -n "DeepSeek V4 Pro.*Tier1|Tier1: DeepSeek|GPT-5.4|DS-out|gpt-5.4" skills\_shared skills\auto-dev`
- `rg -n "sub_session_id|SessionId|500k|token_usage|DEFERRED_due_to_codex_unavailable" skills\_shared skills\auto-dev`
- `rg -n "install-all.ps1|manifest.json|nested-submodule" docs\auto-dev\2026-07-10-skill-meta-flow-control-rules-extended\PLAN.md`

正式分类测试：

- CAT-1：人工表格核对 `SKILL_CORE.md` 与 `MODEL_ROUTING.md` 的 Tier1/Tier2/fallback 完全一致。
- CAT-2：运行 `python skills\_shared\scripts\test_show_session_context.py`，确认 DeepSeek 500k / Codex 250k 阈值未破坏。
- CAT-3：人工检查 §0.10/§0.11 是否覆盖 case A、case B、DETECT_CONTRADICTION、USER_NEEDS_DIGEST。
- CAT-4：用 Q-1..Q-13 的文件集合手算聚类，期望结果为单 pipeline，因为全部高度耦合 `SKILL_CORE.md`。
- CAT-5：grep 旧缩写和旧路由残留，确认入口摘要与共享规则一致。

总回归覆盖：

- `python skills\_shared\scripts\test_show_session_context.py`
- `python skills\_shared\scripts\test_auto_dev_guard.py`
- 对 `SKILL_CORE.md` / `MODEL_ROUTING.md` / `WORKFLOW.md` / `auto-dev\SKILL.md` 做模型路由一致性 grep。
- 验证 docs 产物不引用 forbidden scope 文件作为修改目标。

## 7. 高风险检查点

CP-1：CAT-1 后立即检查所有 Tier1/Tier2 表。不能等到最后，否则后续章节会基于旧路由继续扩散。

CP-2：CAT-2 后立即验证 `sub_session_id=<pipeline_id>` 与现有 `dispatch.ps1 -SessionId` 的映射说明，避免文档写出无法执行的字段。

CP-3：CAT-3 后立即检查“不阻塞主 session”和“TDD 串行门禁”是否同时成立，不能把后台运行误写成可以跳过阶段等待。

CP-4：CAT-4 后立即跑 file-overlap 聚类自检，确认 Q-1..Q-13 因共享 `SKILL_CORE.md` 保持单 pipeline，不被错误拆成并行。

CP-5：CAT-5 后立即 grep 旧命名、旧 GPT-5.4/DeepSeek Tier1 文案，防止入口摘要和共享规则互相矛盾。

## 8. 风险、回滚策略与非目标

风险：

- HIGH：Q-13 swap 与现有文档旧路由冲突面大，漏改会导致 planner/reviewer 派反。
- HIGH：`_shared\SKILL.md` 不存在，若强行列入 files_in_scope 会造成实现阶段阻塞。
- HIGH：跨 provider session 复用容易被误解为共享 cache；实际只能统一 orchestrator session id。
- MEDIUM：DeepSeek 500k 是用户粗粒度阈值，真实模型窗口可能小于该值。
- MEDIUM：后台 sub-agent 不阻塞规则可能被误写成“不等结果也能推进下一阶段”。
- LOW：命名“长而清”未定义硬字符上限，reviewer 只能按语义判断。
- LOW：token_usage 明细依赖各 runner/报告实际可观测字段，部分条目可能只能估算。

回滚策略：

- 每个 CAT 独立 commit；发现问题时只回滚对应 CAT commit。
- 若 CAT-1 路由表出错，优先回滚 CAT-1 后重做，不继续后续 CAT。
- 若 CAT-2 session 规则无法用现有 `-SessionId` 承载，回滚 CAT-2 文档新增，改为先开新 pipeline 设计 dispatcher 字段。
- 若测试失败只涉及文档 grep 残留，定点修正，不回滚全部。
- 不使用 `git reset --hard`；只用精确 revert 或后续修正 commit。

非目标：

- 不实现新业务功能。
- 不修改任何业务源码。
- 不修改 `install-all.ps1` / `manifest.json`。
- 不处理 nested-submodule-restructure 脏文件。
- 不 push、不 merge、不 release。
- 不承诺跨 OpenAI/DeepSeek provider 的真实 cache 命中率，只规范 orchestrator session id 和 token 报告。

## 9. 仍需用户澄清的问题

AMBIQUITY_RAISED：

1. `skills\_shared\SKILL.md` 不存在。是否接受用 `skills\auto-dev\SKILL.md` 作为 Q-11 入口引用同步文件？还是需要新建 `_shared\SKILL.md`？
2. Q-13a 的“同一 session/cache”是否接受当前落地解释：orchestrator 层统一 `sub_session_id=<pipeline_id>`，Codex 和 DeepSeek provider 内部分别维护 cache，不保证跨 provider cache 命中？
3. Q-11 “长而清命名”是否需要硬字符上限？当前计划是不设上限，只要求全词或中文、禁缩写、看名字能知道派给谁和改什么。

structured report：

```text
[planner:codex model=gpt-5.5 effort=high] PLAN.md done.
paths=G:\ai-toolkit\docs\auto-dev\2026-07-10-skill-meta-flow-control-rules-extended\{PLAN.md,plan.meta.json}
categories=CAT-0 + CAT-1 + CAT-2 + CAT-3 + CAT-4 + CAT-5
steps=10
ac_count=17 (Q-1..Q-13 + Q-13a/b/c)
risks=HIGH_count 3
files_in_scope=4 (SKILL_CORE.md + MODEL_ROUTING.md + WORKFLOW.md + auto-dev/SKILL.md)
q13_swap=Codex_plan_DeepSeek_review_Codex_code_review
session_strategy=per_pipeline_one_sub_session_id
token_threshold=500k
fallback=L0_ideal_to_L1_deferred_to_L2_single_tier
```