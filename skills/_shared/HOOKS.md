# Hooks — 强制门禁清单

> 本文档定义 auto-dev 的**强制门禁钩子**。
>
> **两层执行**：
> - **Prompt 层** — SKILL.md 和 SKILL_CORE.md 中的钩子检查点（模型自觉遵守）
> - **System 层** — `scripts/auto_dev_guard.py` + Claude Code hooks 配置（系统级阻断）
>
> 总体原则：**Skill 说明流程，STATE.json 记录阶段，agent_dispatcher 调用代理，Hook 阻止违规。**

---

## 一、STATE.json 阶段枚举

| 阶段 | 含义 | 允许的动作 |
|---|---|---|
| `intake` | 初始化 | 需求澄清、创建 STATE.json |
| `research` | 调研中 | 文件读取、调研代理调用 |
| `planning` | 计划中 | 调用 Codex planner，禁止编辑源码 |
| `plan_review` | 计划审查 | 主编排 review 计划 |
| `development` | 开发中 | 允许编辑源码 |
| `testing` | 测试中 | 允许编辑测试文件、修复 bug |
| `acceptance` | 验收中 | 只读 + 验收报告 |
| `fixing` | 修复中 | 允许编辑源码（限定范围） |
| `integration` | 集成中 | 合并、集成测试 |
| `verification` | 验证中 | 运行验证命令 |
| `done` | 完成 | 只读 |
| `blocked` | 阻塞 | 只读，等待解除阻塞 |

---

## 二、System 层：PreToolUse 四大强制门禁

由 `scripts/auto_dev_guard.py` 实现，通过 Claude Code hooks 系统调用。

### Gate 1：未批准计划前禁止修改源码

- **触发**：工具为 Write / Edit / MultiEdit，目标路径在 `app/` `src/` `lib/` `core/` `packages/` 下
- **检查**：
  - `current_phase` ∈ {development, fixing, testing}
  - `plan_status` = "approved"
  - `plan_file` 存在
  - `plan.meta.json` 存在
  - `plan.meta.json.created_by` = "codex-planner"
  - `plan.meta.json.plan_status` = "approved"
- **拒绝** → `当前任务尚未进入可开发阶段。请先完成调研、需求确认，并通过 Codex planner 生成并批准 plan.md。`

### Gate 2：主编排者不能直接写正式计划

- **触发**：工具为 Write / Edit / MultiEdit，目标文件为 `plan.md` 或 `plan.meta.json`
- **检查**：主编排者角色
- **拒绝** → `正式计划必须由 planner_owner 指定的计划代理生成。主编排者只能生成 plan-input.md、REQUIREMENTS.md、CODE_CONTEXT.md、DECISIONS.md。`
- **允许**：主编排者调用 `agent_dispatcher plan --planner codex --input <plan-input.md> --output <plan.md>`

### Gate 3：没有验证报告禁止完成/提交/合并/发布

- **触发**：Bash 命令包含 `git commit` / `git merge` / `git push` / `release` / `assembleRelease` / `publish`，或修改 STATE.json 为 `done`
- **检查**：
  - `verification-report.md` 存在
  - `VERIFIED_COMMIT` 存在
  - `VERIFICATION_COMMAND` 存在
  - `EXIT_CODE` = 0
  - `RESULT_FILE` 存在
  - `verification_status` = "passed"
- **拒绝** → `请先完成验证再提交/合并/发布。`

### Gate 4：禁止编排者搬运长文档

- **触发**：Write / Edit / MultiEdit 到 `plan.md` `implementation.md` `test-report.md` `review.md` `independent-review.md`
- **检查**：主编排者角色
- **拒绝** → `这是只读产物文件。主编排者不得覆盖。由原责任代理维护。`
- **允许**：记录文件路径 + 1~3 句话摘要 + 风险 + 下一代理 + 下一输入文件

---

## 三、System 层：Stop Hook（轻量提醒）

- **触发**：Claude Code 每次停止响应
- **行为**：只提醒，不阻断
  - 当前阶段不是 done → 提醒任务未完成
  - 验证报告不存在 → 提醒勿宣称完成
- **注意**：Stop Hook **不作为主要门禁**，真正的阻断在 PreToolUse

---

## 四、System 层：UserPromptSubmit Hook（自动初始化）

- **触发**：用户输入包含 `auto-dev` `开发` `修复` `重构` `实现` `测试` 等关键词
- **行为**：
  - STATE.json 不存在 → 自动创建，初始化阶段为 `intake`
  - STATE.json 存在 → 注入流程提醒

---

## 五、Prompt 层钩子（模型自觉 + Skill 提示词强制执行）

以下钩子依赖 SKILL.md / SKILL_CORE.md 中的提示词 + 主编排者自觉：

| 钩子 | 触发时机 | 规则 |
|---|---|---|
| `plan_must_be_codex` | CATEGORY_PLANNING 阶段 | 主编排者禁止自己写 PLAN.md，必须调用 Codex 子代理。Gate 2 提供系统级兜底。 |
| `codex_output_visible` | Codex 子代理返回 | Codex 输出必须展示在主编排者输出中，至少展示 STATUS/SUMMARY/CONFIDENCE/RISK。 |
| `stage_entry_check` | 进入新阶段 | 检查前置产物齐全，缺失则禁止进入。 |
| `pre_commit_gate` | git commit 前 | 检查 VERIFICATION_REPORT 存在且通过。Gate 3 提供系统级兜底。 |
| `max_retry_gate` | 第 3 次相似修复 | 强制升级假设/模型/会话。 |
| `parallel_safety_check` | 启动并行类别 | 检查依赖图无冲突。 |
| `post_task_reflection` | 任务完成 | 写 AUTO_DEV_LEARNINGS.md。 |

---

## 六、Claude Code Hooks 配置

在项目 `.claude/settings.json` 或全局 `~/.claude/settings.json` 中配置：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "command": "python \"{SKILL_PATH}/scripts/auto_dev_guard.py\" pretooluse \"{PROJECT_DIR}/.ai-work\""
      }
    ],
    "Stop": [
      {
        "command": "python \"{SKILL_PATH}/scripts/auto_dev_guard.py\" stop \"{PROJECT_DIR}/.ai-work\""
      }
    ],
    "UserPromptSubmit": [
      {
        "command": "python \"{SKILL_PATH}/scripts/auto_dev_guard.py\" userpromptsubmit \"{PROJECT_DIR}/.ai-work\""
      }
    ]
  }
}
```

> `--orchestrator=codex|reasonix` 模式使用 `.collab-work` 替代 `.ai-work`。

---

## 七、违规处理

1. PreToolUse 门禁拒绝 → 工具调用被系统阻断，返回原因
2. Prompt 层钩子违规 → 主编排者应立即停止，回退操作，按正确流程重做
3. 同一钩子连续 2 次违规 → 记录到 `AUTO_DEV_LEARNINGS.md`，考虑强化门禁

---

## 八、Reasonix 钩子方案

Reasonix 目前没有原生 PreToolUse hook 系统。在 Reasonix 中通过以下方式实现同等门禁：

### 方式 1：Prompt 层强制（已内置）

SKILL_CORE.md 第 8 节列出了全部 4 个 System 层门禁规则。在 Reasonix 中，这些规则作为**不可跳过的强制指令**嵌入 SKILL.md 提示词。主编排者在每次工具调用前必须在思考中自检：

```
自检清单（每次 Write/Edit/MultiEdit 前）：
□ 目标路径是否在 app/src/lib/core/packages 下？
  → 是 → current_phase 必须是 development/fixing/testing？
  → 是 → plan_status 必须是 approved？
□ 目标文件是否是 plan.md / plan.meta.json？
  → 是 → 主编排者禁止直接写，必须调用 Codex 子代理
```

### 方式 2：通过 `auto_dev_guard.py` 手动调用

在 Reasonix 会话中，主编排者可以在关键操作前手动运行 guard：

```bash
echo '{"tool_name":"Edit","file_path":"src/main.py"}' | python scripts/auto_dev_guard.py pretooluse .ai-work
```

返回 `{"decision": "deny", ...}` 则禁止操作。

### 方式 3：未来 — Reasonix 原生 Hook

如果 Reasonix 后续支持 hooks，可以在 `~/.reasonix/config.json` 中配置：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "command": "python \"G:\\ai-toolkit\\skills\\_shared\\scripts\\auto_dev_guard.py\" pretooluse \"{PROJECT_DIR}\\.ai-work\""
      }
    ]
  }
}
```

## 九、其他 Skill 的钩子扩展

任何需要严格执行的 Skill 都可以引用本 Hook 体系：

1. 复制 `auto_dev_guard.py` 到目标 Skill 的 `scripts/` 目录
2. 在 Skill 的 SKILL.md 中声明使用的钩子
3. 在 Claude Code hooks 配置中添加对应的 PreToolUse 规则
4. 自定义 SOURCE_DIRS / RESTRICTED_COMMANDS 等常量以匹配 Skill 需求
