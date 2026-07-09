# DEFERRED_CODEX_REVIEW.md — Codex 不可用证据 + L1 fallback 路径（增强版）

> 本批 pipeline 一开始即确认 Codex CLI 卡死,**跳过 PLAN_REVIEW**,**直接派 tester 写 TEST_TARGET.md** (Q-1 + Q-9 + 上一批 BUG-6 经验)。
>
> 用户「拍 codex 出 plan」后又 retry 一次, 仍 exit_code=-1。**L1 fallback 启动**(deepseek-planner)。

---

## 1. Codex 不可用证据

### 1.1 上一批末次 Codex run (上一会话内存留)

```json
{
  "exit_code": -1, "status": "failed",
  "run_id": "codex-review-20260709-230305"
}
```

### 1.2 本批首次 probe（首次派 codex-plan）

```bash
# bash b00dy16x4
pwsh ... dispatch.ps1 -Action codex-plan ... -ProblemStatement "..."
```

**失败原因**: `run-codex-plan.ps1` 不接受 `-ProblemStatement` 参数（NamedParameterNotFound）。
这是 **dispatch.ps1 参数错配**，不是 codex 端 fail。

### 1.3 本批 retry probe（修对参数）

```bash
# bash bf1rj3rqg
pwsh ... dispatch.ps1 -Action codex-plan ... (no -ProblemStatement) -Model gpt-5.5 -Effort high
```

修对参数后 retry：
- 新建 `REQUIREMENTS.md` 到 `G:\ai-toolkit\.ai-work\runs\skill-meta-flow-control-rules-extended-2026-07-10\REQUIREMENTS.md`（runner §26 check）
- 移除 `-ProblemStatement`（runner 不接受）

**结果**（CURRENT_CODEX_RUN.json）：

```json
{
  "run_id": "codex-plan-20260710-015543",
  "run_label": "codex-plan",
  "status": "failed",
  "exit_code": -1,
  "elapsed_seconds": 187,
  "task_dir": "G:\\ai-toolkit\\.ai-work\\runs\\skill-meta-flow-control-rules-extended-2026-07-10"
}
```

**结论**: Codex CLI **真卡死 confirmed（3 次连续 fail）**。
- 第一次（上一批末次）：codex-review exit -1
- 第二次（本批首次）：dispatch 参数错配（已修）
- 第三次（本批 retry）：codex-plan exit -1

---

## 2. 走 L1 fallback（Q-1 + Q-13 + DEFERRED handler + α 决策）

按 SKILL_CORE §0.7.2 + 本批 Q-1 + 上一批 BUG-6 经验 + 用户 C-2 (α) 决策：

1. **跳过 PLAN_REVIEW 阶段**: 写本文件 `DEFERRED_CODEX_REVIEW.md` 标 `reviewer_status = deferred_due_to_codex_unavailable`，**不解锁 developer**。
2. **L1 fallback dispatcher**: 派 `[planner:deepseekV4pro]` (subagent_type=`deepseek-planner`, model=fable, effort=max) 出 PLAN.md。
3. tester 完成后 → developer → tester 跑测试 → reviewer (异构底线 CODE_REVIEW 工位宽松: deepseek-reviewer fallback) → ACCEPTANCE。

---

## 3. reviewer_status 字段

```
reviewer_status: deferred_due_to_codex_unavailable
reviewer_status_l1_fallback: active
reviewer_status_l1_dispatcher: deepseek-planner
```

---

## 4. 用户决策（C-2 α）

用户决策：**Q-13 理想 Tier1（Codex plan）+ Q-1 fallback 并存**。
- 当前 Codex 不可用 → 本批强制 L1 fallback
- 用户「拍 codex 出 plan」实测一次仍 fail → 立即转入 L1 fallback
- **L2 单 agent fallback**（Codex + DeepSeek 都卡）：不启用（DeepSeek 可用）

---

## 5. Session 复用（Q-13a 落地执行）

同 pipeline 内所有 sub-agent 沿用同一 session_id：
```
sub_session_id = skill-meta-flow-control-rules-extended-2026-07-10
```

dispatcher 转发 `codex exec ... resume <session_id>` 时用此值。DeepSeek 端由 litellm / DeepSeek 自维护 prompt cache；orchestrator 视角同 session_id。

---

## 6. L1 fallback dispatcher 已启动

| sub-agent | type | model | effort | task |
|---|---|---|---|---|
| `[planner:deepseekV4pro]` | deepseek-planner | fable | max | 出 PLAN.md + plan.meta.json |

派单后立即：
- 跑完 → PLAN_REVIEW 阶段 DEFERRED → tester first (Q-1)
- developer 接力实施 → tester 跑测试 → reviewer 审 diff → ACCEPTANCE

---

## 7. 后续条件

- 若 Codex CLI 之后可用（status=completed, exit_code=0）→ 下一批 pipeline 可恢复 L0 路径。
- 本批全程：`deepseek-planner` 出 plan + `deepseek-reviewer` 异构 fallback 审 CODE_REVIEW diff。

---

## 8. 严禁

- 严禁「等等 Codex 也许就好了」→ 不派单 / 不 poll → user driven only。
- 严禁把 CODE_REVIEW 异构底线也降级到同源 → 那是 Q-4 严禁的反模式（保留 deepseek-reviewer fallback）。
- 严禁 sub-agent 直接 call user prompt；通过 `AMBIGUITY_RAISED` 字段汇报，主编排代问 (Q-6)。
- 严禁 dispatch 重复 codex-plan 探测（已确认 3 次 fail，除非用户明确再试一次）。
