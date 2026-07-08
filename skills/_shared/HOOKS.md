# Hooks — 强制门禁清单

> 本文档定义 auto-dev 的**强制门禁钩子**。
>
> **两层执行**：
> - **Prompt 层** — SKILL.md 和 SKILL_CORE.md 中的钩子检查点（模型自觉遵守）
> - **System 层** — `scripts/auto_dev_guard.py` + Claude Code hooks 配置（系统级阻断）
>
> 总体原则：**Skill 说明流程，STATE.json 记录阶段，agent_dispatcher 调用代理，Hook 阻止违规。**

> **任务模式兼容**：对于 IronWill 这类已经迁移到 `.ai/tasks/<TASK-ID>/STATUS.md` 的项目，guard 会在未找到可用 `.ai-work/STATE.json` 时自动发现最新活跃任务，并对该任务应用门禁。

---

## 一、STATE.json 阶段枚举

| 阶段 | 含义 | 允许的动作 |
|---|---|---|
| `intake` | 初始化 | 需求澄清、创建 STATE.json |
| `research` | 调研中 | 文件读取、调研代理调用 |
| `planning` | 计划中 | 调用 DeepSeek V4 Pro planner / OpenCode-OMO plan wrapper，禁止编辑源码 |
| `plan_review` | 二次计划审查 | 独立审查 `PLAN.md`，必须产出 `PLAN_REVIEW.md` 并批准 |
| `development` | 开发中 | 允许编辑源码 |
| `testing` | 测试中 | 允许编辑测试文件、修复 bug |
| `acceptance` | 验收中 | 只读 + 验收报告 |
| `fixing` | 修复中 | 允许编辑源码（限定范围） |
| `integration` | 集成中 | 合并、集成测试 |
| `verification` | 验证中 | 运行验证命令 |
| `done` | 完成 | 只读 |
| `blocked` | 阻塞 | 只读，等待解除阻塞 |

---

## 二、System 层：PreToolUse 强制门禁

由 `scripts/auto_dev_guard.py` 实现，通过 Claude Code hooks 系统调用。

### Gate 1：未批准计划 / 未通过二次计划审查前禁止修改源码

- **触发**：工具为 Write / Edit / MultiEdit，目标路径在 `app/` `src/` `lib/` `core/` `packages/` 下
- **检查**：
  - `current_phase` ∈ {development, fixing, testing}
  - `plan_status` = "approved"
  - `plan_file` 存在
  - `plan.meta.json` 存在
  - `plan.meta.json.created_by` ∈ {`deepseek-v4-pro-planner`, `opencode-omo-hyperplan`, `planner`}
  - `plan.meta.json.plan_status` = "approved"
  - `plan_review_status` = "approved"
  - `PLAN_REVIEW.md` 或 `plan_review_file` 存在
- **拒绝** → `当前任务尚未进入可开发阶段。请先完成调研、需求确认、计划生成，并通过二次计划审查。`

### Gate 2：主编排者不能直接写正式计划

- **触发**：工具为 Write / Edit / MultiEdit，目标文件为 `plan.md` 或 `plan.meta.json`
- **检查**：正式计划必须由计划代理生成；主编排者只能生成 `plan-input.md`、`REQUIREMENTS.md`、`CODE_CONTEXT.md`、`DECISIONS.md`
- **拒绝** → `正式计划必须由 plan agent 生成。默认计划代理：DeepSeek V4 Pro；OpenCode + oh-my-openagent 可用 hyperplan / 项目包装层 run-opencode-plan。主编排者不得直接写 PLAN.md。`
- **允许**：主编排者调用 DeepSeek V4 Pro planner、Codex review、`run-opencode-plan` / `run-omo-plan` / OMO `hyperplan`，但这些入口必须写出运行目录、`status.json` 和日志路径。

#### Plan / Review Agent 路由

**默认计划**：DeepSeek V4 Pro planner。  
**默认二次计划审查**：Codex reviewer；`PLAN.md` 生成后优先调用 Codex 输出 `PLAN_REVIEW.md`。Codex CLI 只能复用 Codex 自己的会话 / resume；跨 Claude/Codex/OpenCode 时通过文件交接。  
**Codex 额度不足**：不阻塞当前开发；必须记录 `CODEX_STATUS.json` 与 `DEFERRED_CODEX_REVIEW.md`，并标记 `plan_review_status = deferred_due_to_codex_quota`。延期记录仅用于审计追溯，不自动补跑。  
**GPT 增强**：只在有额度时启用，用于更高风险的计划复核、关键代码审查、复杂 bug 二次判断和最终兜底；不是必经流程。  
**DeepSeek 计划入口不可用**：进入 `blocked`，原因 `NO_PLAN_AGENT_AVAILABLE`。禁止主编排者直接写正式 PLAN.md 或放行开发。

### Gate 3：没有最终验证报告禁止完成/合并/发布

- **触发**：Bash 命令包含 `git merge` / `git push` / `release` / `assembleRelease` / `publish`，或修改 STATE.json 为 `done`
- **不触发普通 step commit**：`commit_step_gate` 要求每个原子修改及时 `git commit`，普通 step commit 只需要对应阶段的局部验证；不得被最终验证报告门禁阻断。
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

### Task Gate：`.ai/tasks` 模式下缺计划或缺二次计划审查时禁止绕过

- **触发**：guard 自动发现 `.ai/tasks/<TASK-ID>/STATUS.md` 为当前活跃任务，且该任务缺少 `PLAN.md`
- **拒绝 1**：任何 `Agent` / `SendMessage` 工具调用
  - **原因**：禁止拿普通后台子任务代替正式计划代理或二次审查代理
- **拒绝 2**：任何非只读 `Bash` 命令
  - **允许**：显式运行 DeepSeek V4 Pro plan/review wrapper、`run-opencode-plan`、`run-omo-plan`、`hyperplan`；以及 `rg` / `Get-Content` / `git status` 等只读检查
- **拒绝 3**：任何源码 `Write` / `Edit` / `MultiEdit`
  - **原因**：当前任务还没有计划代理生成的 PLAN.md 或没有通过二次计划审查，不能进入开发

这层门禁的目标不是替代完整状态机，而是防止主编排者在 `.ai/tasks` 模式下口头承认漏了计划/审查，却继续靠后台 Agent 或其他命令往前走。

### Gate 5: 工作树卫生门禁 (working_tree_hygiene)

**目的**：防止 Agent 在 working tree 累积未提交改动导致 linter/编辑器/session 中断时全丢（实测 100+ 行代码丢失事件）。

- **触发**：
  - Agent 报告"完成" / "已 commit" / "可验收"
  - 用户切到新 Agent 接手前
  - 任何 `Bash` 命令包含 `git commit` / `git push` / `git merge`
  - Agent 退出 / session 切换
- **检查**：
  1. 读取 `git status --short` 输出
  2. 如果有 `M` 或 `??` 标记的**未相关**改动（不在 `git add` 范围），阻断并提示：
     ```
     ⛔ working tree 有未提交改动:
     M  app/src/main/java/com/ironwill/app/LockWindowManager.kt
     ?? scripts/auto-code-android-dev/_codex-runtime.ps1
     
     处理方式：
     A) 如果属于当前任务: git add + git commit
     B) 如果是 pre-existing 改动: 通知用户决定（不要自动 commit）
     C) 如果是误改: git restore <file> 或 git clean -fd
     ```
  3. 阻断"完成"声明，要求先 commit 或 revert
- **允许**：
  - 只读 `git status` / `git log` / `git diff` 检查
  - `git add` + `git commit`（前提是精确指定文件，不用 `.` 或 `-A`）
  - `git restore <file>` 撤销错误改动
- **失败行为**：阻断 commit、阻断"完成"声明、阻断 Agent 退出

### Gate 6: Agent dispatch 缺 `model` 参数时阻断 (agent_dispatch_model_required)

- **触发**：工具为 `Agent`，且 hook_input 中 `model` 字段为空或未设置
- **检查**：
  - Agent 工具的 `model` 参数是否显式传入
  - 如果 `model` 为空/未传 → 允许（主编排默认 = MiniMax-M3，不需要 model 参数）
  - 但对于已知角色 agent type（`auto-dev-developer`, `auto-dev-tester`, `auto-dev-researcher`, `auto-dev-emulator-tester`, `auto-dev-brainstorm`, `auto-dev-writing`），如果 `model` 为空 → **阻断**
- **允许**：主编排自身的 Agent 调用（无 model 参数，默认 MiniMax-M3）
- **拒绝** → `GATE 6 BLOCKED: auto-dev 子代理 dispatch 缺少 model 参数。必须显式传入 model (sonnet/opus/haiku/fable)，按角色选择。planner=fable(deepseekV4pro), developer=sonnet|opus, tester=sonnet|haiku, reviewer=codex(CLI).`
- **注意**：此门禁为**轻量阻断**（仅对已知 auto-dev agent type 生效），不能替代 prompt 层钩子自检。如果 guard.py 未更新或不支持解析 Agent tool 的 model 参数，此门禁退化为 prompt 层强制执行。

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
| `plan_must_be_agent` | CATEGORY_PLANNING 阶段 | 主编排者禁止自己写 PLAN.md，默认调用 DeepSeek V4 Pro planner 或 OpenCode/OMO hyperplan。Gate 2 提供系统级兜底。 |
| `plan_review_must_pass` | PLAN.md 生成后、开发前 | 所有 auto-dev 任务必须二次计划审查。无 `PLAN_REVIEW.md` 或 `plan_review_status != approved` 时禁止进入开发。 |
| `planner_output_visible` | 计划代理返回 | DeepSeek/OpenCode/OMO/可选 GPT 输出必须展示在主编排者输出中，至少展示 STATUS/SUMMARY/CONFIDENCE/RISK。 |
| `agent_runtime_visible` | 启动 DeepSeek/OpenCode/OMO/可选 GPT plan/review/implement 脚本 | 启动后必须立刻产出 `status.json` + stdout/stderr 日志路径；超过 600 秒无活动必须标记 `silent`，达到脚本上限必须标记 `timed_out`。 |
| `stage_entry_check` | 进入新阶段 | 检查前置产物齐全，缺失则禁止进入。 |
| `pre_commit_gate` | 最终合并/发布/标记 done 前 | 检查 VERIFICATION_REPORT 存在且通过。普通 step commit 由 `commit_step_gate` + Gate 5 约束。 |
| `max_retry_gate` | 第 3 次相似修复 | 强制升级假设/模型/会话。 |
| `parallel_safety_check` | 启动并行类别 | 检查依赖图无冲突。 |
| `post_task_reflection` | 任务完成 | 写 AUTO_DEV_LEARNINGS.md。 |
| `raw_outputs_must_be_preserved` | 任一角色生成文档/报告/审查 | 禁止覆盖原始输出；修订只能新增 v2/round2/patch/resolution/superseded 文件。 |

---

## 六、Claude Code Hooks 配置

在项目 `.claude/settings.json` 或全局 `~/.claude/settings.json` 中配置：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python \"%USERPROFILE%\\.agents\\skills\\_shared\\scripts\\auto_dev_guard.py\" pretooluse \"{PROJECT_DIR}\\.ai-work\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"%USERPROFILE%\\.agents\\skills\\_shared\\scripts\\auto_dev_guard.py\" stop \"{PROJECT_DIR}\\.ai-work\""
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"%USERPROFILE%\\.agents\\skills\\_shared\\scripts\\auto_dev_guard.py\" userpromptsubmit \"{PROJECT_DIR}\\.ai-work\""
          }
        ]
      }
    ]
  }
}
```

> `--orchestrator=codex` 可使用 `.collab-work` 替代 `.ai-work`；`--orchestrator=opencode` 可使用 `.omo/auto-dev-work`，但建议仍保留 `.ai-work` 兼容旧脚本。
> **guard 自动跳过**：只有在旧 `.ai-work/STATE.json` 活跃，或自动发现 `.ai/tasks` 活跃任务时才应用门禁；普通会话不受影响。

---

## 七、违规处理

1. PreToolUse 门禁拒绝 → 工具调用被系统阻断，返回原因
2. Prompt 层钩子违规 → 主编排者应立即停止，回退操作，按正确流程重做
3. 同一钩子连续 2 次违规 → 记录到 `AUTO_DEV_LEARNINGS.md`，考虑强化门禁

---

## 八、OpenCode / oh-my-openagent 钩子方案

OpenCode + oh-my-openagent 的核心不是 Claude Code Skill 入口，而是项目级规则注入与生命周期 hooks：

1. **规则注入**：把本 Skill 的核心规则写入项目根 `AGENTS.md` 和 `.omo/rules/auto-dev.md`。OMO 的 rules injection 会在每次 prompt 自动加载这些规则。
2. **计划入口**：复杂任务先用 DeepSeek V4 Pro `hyperplan` / `run-opencode-plan` 产出类别计划，再在 `PLAN_REVIEW` 节点优先调用 Codex 审查；Codex 无额度时记录延期审查。不要直接让 `ultrawork` 从需求跳到改代码。
3. **Team Mode**：允许最多 5 个低耦合类别并行；MiniMax / OpenCode 额度充足时可开到 5 路，但不得强行凑满。共享核心状态、数据库、关键文件、后台服务或跨日/时间逻辑时必须降到 1–2 路。
4. **验证门禁**：OpenCode hooks 如果不能系统级阻断，至少在规则中强制每次声称完成前输出 `git status --short`、验证命令、exit code 和结果文件。
5. **冲突优先级**：项目安全规则 > 本 Skill 流程 > OMO 默认自动推进。`ultrawork` 不能绕过计划、测试、commit hygiene 和最终验证。

推荐 `.omo/rules/auto-dev.md` 内容见本打包目录的 `opencode-omo-bridge/.omo/rules/auto-dev.md`。

## 九、其他 Skill 的钩子扩展

任何需要严格执行的 Skill 都可以引用本 Hook 体系：

1. 复制 `auto_dev_guard.py` 到目标 Skill 的 `scripts/` 目录
2. 在 Skill 的 SKILL.md 中声明使用的钩子
3. 在 Claude Code hooks 配置中添加对应的 PreToolUse 规则
4. 自定义 SOURCE_DIRS / RESTRICTED_COMMANDS 等常量以匹配 Skill 需求

## 十、计划代理启动脚本约定

以下规则不是 Claude 原生 hook 阻断，而是所有 DeepSeek / OpenCode / OMO / 可选 GPT 启动脚本必须满足的运行约定：

1. 每次运行 plan / review / implement，都要创建独立运行目录。
2. 运行目录中至少包含：
   - `status.json`
   - `stdout.log`
   - `stderr.log`
   - `prompt.txt`
3. `status.json` 至少记录：
   - `status`
   - `pid`
   - `started_at`
   - `last_heartbeat_at`
   - `last_activity_at`
   - `silent_for_seconds`
   - `output_file`
   - `stdout_file`
   - `stderr_file`
4. 推荐状态枚举：
   - `starting`
   - `running`
   - `silent`
   - `timed_out`
   - `failed`
   - `completed`
5. 主编排者必须把状态文件和日志文件路径回显给用户，禁止黑箱等待。
