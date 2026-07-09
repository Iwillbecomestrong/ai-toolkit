# PLAN_REVIEW.md — skill meta TDD+流程约束 异构审查 (deepseek-reviewer fallback)

**DECISION: APPROVE_WITH_NOTES**

```
reviewer_role: independent
review_scope: category
reviewed_by: [reviewer:deepseek] (异构 fallback, 代替 [reviewer:codex] 因 Codex CLI 跑时 exit code -1)
reviewed_at: 2026-07-09
PLAN: G:\ai-toolkit\docs\auto-dev\2026-07-09-skill-meta-tdd-flow\PLAN.md
plan.meta.json: G:\ai-toolkit\docs\auto-dev\2026-07-09-skill-meta-tdd-flow\plan.meta.json
```

> 这是流程产物, 不是 skill 系统层。主编排代理 reviewer 落盘。

---

## 1. Acceptance Criteria 评审 (AC1-AC12)

| AC | 评价 | 备注 |
|---|---|---|
| AC1 Gate 1/1.5 阻断源码编辑 | 真能验证 | 建议补 AC1-b: state=测试靶也能阻断 |
| AC2 Gate 7 dispatch echo + AGENT_REGISTRY.json | 真能验证 | 覆盖完整 |
| AC3 dispatch.ps1 codex-review 验证 | 部分可验证 | 建议拆 AC3-a (echo) + AC3-b (CURRENT_CODEX_RUN.json) |
| AC4 Gate 6 拒绝 sonnet | 真能验证 | 依赖 S1.1 新增白名单校验 |
| AC5 PostToolUse 回填 sub_session_id | 依赖 hook 支持 | 建议补降级验收路径 |
| AC6 Stop hook block | **T5-b 缺: `stop_reason=interrupt` 放行路径未测** | 最高风险 |
| AC7 PostToolUse 串行 enforce | soft enforcement | 可接受 |
| AC8 install-agents.ps1 产出 | 真能验证 | 完整 |
| AC9 show_session_context.py model/effort | 正确 | T7 的 effort 可为空应明示 |
| AC10 WORKFLOW.md 无 gpt-5.4 | 纯负向 | 建议 AC10-b grep 确认含新 effort 分层短语 |
| AC11 Codex runner 默认 gpt-5.5 | 纯负向 | 建议正向 grep `$Model = 'gpt-5.5'` |
| AC12 MODEL_QUOTA_CHECK.md.template 无旧模型 | 可接受 | 例外已注明 |

---

## 2. 九节标准格式评审

全部 9 节齐全,填写完整。**缺失**: `plan.meta.json` 无 `risk_level` 字段。

---

## 3. Risks 等级

plan.meta.json 风险表:1 HIGH + 2 MEDIUM + 2 LOW。**综合风险=HIGH**(`handle_stop block` 变更可能阻止用户正常退出 Claude Code)。

**建议**:meta 补充 `"risk_level": "HIGH"`。developer 接力时一并修。

---

## 4. Plan 完整性:26 Steps 覆盖分析

全部 26 Step 覆盖 12 项背景改动。三个覆盖性问题:

(a) **S1.6 与 S2.8 同文件 (SKILL_CORE.md) 冲突**:CAT-2 标可与 CAT-3/4 并行,但 S2.8 必须等 S1.6。
→ 建议:S2.8 前置列标注为 S1.6。

(b) **Gate 6 白名单逻辑**:旧类型 `auto-dev-developer` 因不在新白名单反而**不被 Gate 6 约束**。需确认设计意图。
→ 建议:明确"旧类型兼容"策略——是不检查还是允许。

(c) **install-agents.ps1 line 57 注释**:`Get-ChildItem $destDir\deepseek-*.md` 指向旧文件,新 agent 是 `claude-*.md`。
→ 建议:加 S1.7 修复此注释。

---

## 5. 与 MODEL_ROUTING.md 一致性

**核心矛盾**:SKILL_CORE §0.7 step 4 写 `REVIEW(派 [reviewer:codex] 审 diff)`,但 MODEL_ROUTING.md Tier 1 代码审查是 **DeepSeek V4 Pro**(deepseek-reviewer),Tier 2 才是 Codex。

**解决方案**:在 §0.7 step 4 明确说明 `REVIEW` 指 PLAN_REVIEW 复审,code review 工位另由 §CODE_REVIEW 走(派 deepseek-reviewer Tier 1)。

异构 fallback 一致性 OK。

---

## 6. 与 §0.6.4 串行一致性

Plan 的 meta-flow 一致。但 CAT-1~4 实现前没有 tester 先写 TEST_TARGET.md(meta-change 场景合理,但应明确声明此例外)。

---

## 7. 其他发现

**(7.1) dispatch.ps1 line 98 bug**: `$sessionText = if (...) { 'none' } else { $sessionText }` — else 分支引用未定义变量。
→ 修 dispatch.ps1。

**(7.2) show_session_context.py cmd_init 新增 --effort 改变位置参数语义**:需确认无现有调用者受影响。
→ 本次 agent template 路径下未发现调用方,安全。

**(7.3) T4 的行为说明**:S1.1 实现后 Gate 6 对 deepseek-planner 行为不变但原因变。
→ Plan 中注明即可。

---

## 总结

| 项 | 评价 |
|---|---|
| 整体质量 | 高 — 26 Step 全覆盖,5 类别清晰,风险识别充分 |
| 核心问题 | 6 项 notes, **无 blocker** |
| 需在 DEVELOP 前处理 | issue #1 (AC6 缺 interrupt 测试) + issue #2 (§0.7 vs MODEL_ROUTING.md 矛盾) |
| 推荐决策 | **APPROVE_WITH_NOTES** 进入 developer 接力 |

---

## 6 项 Notes(developer 接力时一并处理)

```
N1. S2.8 (SKILL_CORE 修订) 前置写明依赖 S1.6
N2. Gate 6 兼容旧类型 `auto-dev-*` 的明确策略(不检查 vs 允许)
N3. install-agents.ps1 line 57 注释修 (deepseek-*.md → claude-*.md)
N4. plan.meta.json 补 risk_level: "HIGH"
N5. dispatch.ps1 line 98 bug 修 (else 分支 undefined variable)
N6. §0.7 step 4 明确区分 PLAN_REVIEW 复审 vs CODE_REVIEW 工位 (后者 Tier 1 是 deepseek-reviewer)
```

---

## structured report (from reviewer)

```
STATUS: PASS
OUTPUT_FILE: G:\ai-toolkit\docs\auto-dev\2026-07-09-skill-meta-tdd-flow\PLAN_REVIEW.md
SUMMARY: PLAN 整体质量高, 26 steps 全覆盖, 5 类别划分合理。6 项 notes: AC6 缺 interrupt 测试 (最高风险)、§0.7 与 MODEL_ROUTING.md 代码审查工位矛盾、CAT-2 并行图与实际文件依赖不一致、dispatch.ps1 line 98 bug、AC10/11/12 纯负向验证、plan.meta.json 缺 risk_level。
CONFIDENCE: HIGH
RISK: HIGH
COMMIT: NONE
AGENT_ROLE: reviewer (异构 fallback)
AGENT_SESSION: deepseek-reviewer-fallback-20260709
NEXT_AGENT: developer:minimax (APPROVE_WITH_NOTES 允许进; 6 项 notes 列出要处理)
NEXT_INPUT: G:\ai-toolkit\docs\auto-dev\2026-07-09-skill-meta-tdd-flow\PLAN_REVIEW.md
```
