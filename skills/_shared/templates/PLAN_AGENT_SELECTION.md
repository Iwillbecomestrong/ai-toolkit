# Plan Agent 自动选择 (PLAN_DECISION.json)

> 用法: 主编排者在 CATEGORY_PLANNING 阶段首先执行 fallback 决策, 把结果写入
> `{STATE_DIR}/runs/{task_id}/PLAN_DECISION.json`, 后续 Gate 2 验证会用此文件.

## 决策流程

```bash
STATE_DIR=.ai-work
TASK_ID=20260708-cloze-ux-v3
RUN_DIR=$STATE_DIR/runs/$TASK_ID
mkdir -p $RUN_DIR

DECISION_FILE=$RUN_DIR/PLAN_DECISION.json
echo '{}' > $DECISION_FILE
```

### Step 1: 测试 Codex

```bash
CODEX_TEST=$(echo "Say hi" | codex exec -C . --sandbox read-only --color never -m gpt-5.4 - 2>&1 | head -3)
if echo "$CODEX_TEST" | grep -q "usage limit"; then
    CODEX_AVAIL="false"
    CODEX_REASON="usage limit"
elif echo "$CODEX_TEST" | grep -q "ERROR"; then
    CODEX_AVAIL="false"
    CODEX_REASON="login/auth error"
else
    CODEX_AVAIL="true"
    CODEX_REASON="ok"
fi
```

### Step 2: 测试 Reasonix

```bash
if [ "$CODEX_AVAIL" = "true" ]; then
    REASONIX_AVAIL="skipped"
    REASONIX_REASON="codex available, skipped"
else
    RX_TEST=$(reasonix --version 2>&1)
    if echo "$RX_TEST" | grep -q "Reasonix"; then
        # 进一步检查 DEEPSEEK_API_KEY
        if [ -n "$DEEPSEEK_API_KEY" ]; then
            REASONIX_AVAIL="true"
            REASONIX_REASON="ok"
        else
            REASONIX_AVAIL="false"
            REASONIX_REASON="no DEEPSEEK_API_KEY"
        fi
    else
        REASONIX_AVAIL="false"
        REASONIX_REASON="not installed"
    fi
fi
```

### Step 3: 决策

```bash
if [ "$CODEX_AVAIL" = "true" ]; then
    FALLBACK="codex"
elif [ "$REASONIX_AVAIL" = "true" ]; then
    FALLBACK="reasonix"
else
    FALLBACK="orchestrator_direct"
fi
```

### Step 4: 写决策文件

```bash
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
cat > $DECISION_FILE <<EOF
{
  "task_id": "$TASK_ID",
  "timestamp": "$TIMESTAMP",
  "codex": {"tested": true, "available": $CODEX_AVAIL, "reason": "$CODEX_REASON"},
  "reasonix": {"tested": true, "available": $REASONIX_AVAIL, "reason": "$REASONIX_REASON"},
  "fallback": "$FALLBACK",
  "output": "$RUN_DIR/PLAN.md"
}
EOF
```

## 后续动作

- `fallback=codex` → `scripts/auto-code-android-dev/run-codex-plan.ps1 -ProjectRoot . -TaskDir $RUN_DIR -CategoryId <cat>`
- `fallback=reasonix` → `reasonix run -m deepseek-v4-pro --effort high --no-config "<plan request>"` 提示词指定输出到 `$RUN_DIR/PLAN.md`
- `fallback=orchestrator_direct` → 主编排者直接写, 顶部声明 fallback 原因

## 验证

完成后跑 `python -m json.tool $DECISION_FILE` 确认 JSON 合法.

## 与 STATE.json 集成

可选: 把 `fallback` 字段同步到 `STATE.json` 的 `plan_agent_status` 字段.
但保持 PLAN_DECISION.json 是权威记录, STATE.json 是状态机.
