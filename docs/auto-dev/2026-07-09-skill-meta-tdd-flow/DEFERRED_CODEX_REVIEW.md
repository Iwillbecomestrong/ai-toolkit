# DEFERRED_CODEX_REVIEW.md — Codex Tier1 异构审查延期 (Codex CLI 卡死)

> **状态**:  `reviewer_status = deferred_due_to_codex_unavailable`  
> **触发**: `bsqecdgw0` 真 Codex CLI 调用 exit code -1(`codex exec failed`)  
> **时间**: 2026-07-09  
> **影响 pipeline**: skill meta 改造 (skill-meta-tdd-flow-2026-07-09)  
> **依据**: 按用户的规则**Codex 卡死 = 不降级到 deepseek-reviewer(那丧失异构底线)= 跳 PLAN_REVIEW 阶段, 直接派 tester first**。next skill-meta 流程 iteration 时需把这规则正式写入 `_shared/SKILL_CORE.md` §0.7 (Q-1)。

## 1. 触发详情

```text
$ pwsh dispatch.ps1 -Action codex-review -Effort high
[dispatch] 派 [reviewer:codex] action=codex-review model=gpt-5.5 effort=high session=none ...
codex exec failed with exit code -1. Status: G:\ai-toolkit\docs\auto-dev\...\.codex-runtime\
codex-review-20260709-223717\status.json
```

Codex CLI 启动后立即 exit -1 (不是 timeout,是 startup 阶段崩溃)。不是 quota / rate limit。**判断为 Codex runtime 卡死**。

## 2. 处理动作 (按新规则)

| step | 动作 | 谁 |
|---|---|---|
| 1 | 写本文件 `DEFERRED_CODEX_REVIEW.md`(已完成) | 主编排 |
| 2 | `reviewer_status = deferred_due_to_codex_unavailable` 写入 pipeline state | 主编排 |
| 3 | **不解锁 developer**(这是关键 — 不允许 "降级到 deepseek" 伪异构) | 主编排 |
| 4 | 派 `[tester:minimax]` (effort=medium) 写 TEST_TARGET.md (TDD 头) | 主编排 bg 派 |
| 5 | tester 完成 → developer (`[developer:minimax]`, effort=high) 实现 + atomic commit | 主编排 bg 派 |
| 6 | tester 跑 unit test + 验证 install + hook mock | 主编排 bg 派 |
| 7 | reviewer 审 diff (此阶段异构底线灵活 — Codex 仍不可用 → 派 deepseek-reviewer 审) | 主编排 bg 派 |
| 8 | ACCEPTANCE | 等用户 |

## 3. 何时 retry Codex Tier1 异构审

按"延后不阻塞"原则:
- (a) Codex CLI 恢复正常后 (exit code 0 可以读到输出),用户或主编排主动 retry Tier1。
- (b) 或者用户主动决定"升级到 Tier 2" (出 plan 改 Codex,审 plan 用 deepseek-reviewer) — **那才是真正异构**。但目前 PLAN 已存在 (deepseek-planner 出),所以 Tier 2 升级含义是"销毁现有 PLAN, 派 `[planner:codex]` (Bash `dispatch.ps1 -Action codex-plan -Effort xhigh`) 重出 plan", 然后 deepseek-reviewer 审。

## 4. 与 NEXT_ACTIONS.md 的关系

Q-1 (Codex 卡死 → DEFERRED + skip + tester first) 已经在 `NEXT_ACTIONS.md` 排队,等当前 pipeline ACCEPTANCE 后,跟下一批 (Q-1~Q-5) 一起出 PLAN + 走 TDD+reviewer 流程,在 developer 落地 SKILL_CORE 时一并写入 §0.7。

## 5. `CURRENT_CODEX_RUN.json` 与 `.codex-runtime/codex-review-20260709-223717/`

保留以 audit:
- `CURRENT_CODEX_RUN.json` 含 `model=gpt-5.5 effort=high session=none exit_code=-1 status=failed`
- `.codex-runtime/codex-review-20260709-223717/status.json` 是 Codex runtime 自己写的失败状态
- `.codex-runtime/codex-review-20260709-223717/invoke-codex.ps1` 是 Codex 调用脚本

不要清空,留作 audit 证据。
