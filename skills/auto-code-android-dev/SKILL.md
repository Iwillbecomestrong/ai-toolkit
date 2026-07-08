---
name: auto-code-android-dev
description: IronWill Android 项目批量开发入口。基于全局 auto-dev 编排框架，增加 Android 专用环境检查、模拟器测试、ADB 验证与 EMULATOR_TEST 阶段恢复。
argument-hint: "<需求、Bug 现象与预期结果>"
disable-model-invocation: true
allowed-tools: Read Write Edit Glob Grep Bash Agent SendMessage
---

# Auto Code Android Dev

## ⛔ 第一步 —— 必须先读共享核心 + auto-dev 入口（违反此条 = 流程错误）

**在回复用户之前**，立即用 Read 工具完整读取以下 5 个文件。不读完、不展示关键规则摘要，**禁止**进入任何阶段：

| # | 文件 | 内容 |
|---|---|---|
| 1 | `../_shared/SKILL_CORE.md` | 核心规则、阶段路由、状态文件 schema、主编排角色 |
| 2 | `../_shared/WORKFLOW.md` | 状态机、角色模型、生产线、并行策略、返工闭环 |
| 3 | `../_shared/HOOKS.md` | 强制门禁清单、Gate 1-5、Claude Code hooks 配置 |
| 4 | `../_shared/MODEL_ROUTING.md` | 默认模型分工、强制规则、审查分轮、生产线规则 |
| 5 | `../auto-dev/SKILL.md` | 通用编排入口、编排后端选择、类别分组、工作树 commit 规范 |

> 本文件只是 **Android 专用差异**（ADB、Gradle、模拟器、APK、Logcat、设备验收）。
> 完整流程、状态机、门禁、模型路由全部定义在上述 5 个文件中。
> **跳读共享文件直接执行 = 必然出错 = 返工。**

用户需求：

$ARGUMENTS

> **基础框架**：本 skill 与 [`auto-dev`](../auto-dev/SKILL.md) 共用 `../_shared/` 下的核心文件（SKILL_CORE、WORKFLOW、HOOKS、ROUTING 等）。Android 专用差异仅在本文件定义。

## ⛔ 铁律——禁止跳过（继承自 auto-dev）

以下规则**不可协商**，即使任务看起来"很简单"：
0. **责任身份不共享对话，只复用同一责任身份的原会话**。Planner 与 plan reviewer 是不同责任身份，不是同一个人/会话：默认 planner 由 DeepSeek V4 Pro 承担，plan reviewer 通常由 Codex 承担。Plan reviewer 只提审查意见；planner 拥有 PLAN 的最终裁决与修订权。不同责任身份默认不同会话/子会话/CLI run；不得在同一个对话里先写计划又审自己的计划，或先开发又审自己的代码。复用规则是：谁开发谁返工，谁发现谁复验关闭；reviewer/tester 发现的问题必须回到对应 owner 处理：计划问题回 planner 修订 PLAN，代码问题回 developer 返工，原发现者复验关闭。跨身份只通过 `PLAN.md`、`PLAN_REVIEW.md`、`PLAN_REVIEW_RESOLUTION.md`、`HANDOFF.md`、`TEST_REPORT.md`、commit 交接。
1. **必须走完整流程**：ENV_CHECK → REQUIREMENTS → RESEARCH → CATEGORY_PLANNING → DEVELOPMENT → TESTING → VERIFICATION
2. **不得自行判断"不需要 auto-dev"**。只要通过 /auto-code-android-dev 调用，就必须执行完整流程
3. **PLAN.md 必须由计划代理生成，并且必须经过二次计划审查**。默认计划模型是 DeepSeek V4 Pro，二次计划审查由 Codex 承担；OpenCode + oh-my-openagent 场景可用 hyperplan / plan wrapper 承载。主编排者永远不能自己写正式 PLAN.md
4. **必须完整阅读 `../_shared/SKILL_CORE.md`**
5. **用户中途补充信息 ≠ 退出流程**。即使用户插话补充需求、提问或纠正，流程不会取消。收到任何消息后，第一步永远是读取 STATE.json 恢复状态，从当前阶段继续推进
6. **分类由主编排者亲自做，计划每类独立出**。CATEGORY_DISCOVERY 是编排决策，严禁委托计划代理。BATCH_PLAN_BY_SUBAGENT = 每类一个独立计划代理调用（默认 DeepSeek V4 Pro planner，OpenCode/OMO 可用 hyperplan），严禁一个代理包揽全部类别
7. **用户反馈 bug/问题/没改好 ≠ 直接改代码**。即使用户说"这个没改好"、"XX 还是不行"、"闪退"、"UI 不对"，也**必须**先写 `plan-input.md` 或 `PLAN_PATCH.md` 描述问题根因和修改方案，然后交 DeepSeek V4 Pro planner 审查或生成修订计划。主编排者**禁止**直接根据用户反馈动手改代码。即使"只改一行"、"只是加个判断"也不得跳过。必须先产出书面方案 → planner 审查批准 → 再改代码。
8. **子代理派遣必须显式声明角色+模型**。每次用 Agent 工具 dispatch 子代理，**label 必须**用 `[角色:模型] 任务描述` 格式（见 `../_shared/SKILL_CORE.md` §5.2）。禁止省略模型名。主编排者自身**不是** planner、**不是** developer、**不是** reviewer——这些角色必须通过 Agent 工具派遣对应模型的子代理执行。

## ⛔ Android 工作树 + 编译 强约束

**继承自 auto-dev 工作树 commit 规范，Android 项目额外加编译验证。**

### `android_commit_step_gate`（每步 commit 前）

任何 Kotlin/XML 修改后，在 `git commit` **之前**必须：

```bash
# 1. 编译验证（修改没破坏现有代码）
./gradlew :app:compileDebugKotlin 2>&1 | tail -5
# 2. 验证本次修改范围
git status --short
# 3. 精确 add + commit
git add <精确文件>
git commit -m "fix(alarm): ..."
```

如果 `compileDebugKotlin` 失败 → 修代码，**不得** commit 失败状态。

### `apk_timestamp_check`（安装前强制）

```bash
# 验证 APK 比源码新
ls -la app/build/outputs/apk/debug/app-debug.apk
find app/src/main -name "*.kt" -newer app/build/outputs/apk/debug/app-debug.apk
# 如果有更新的 kt 文件, 重新 build:
./gradlew :app:assembleDebug
```

如果源代码比 APK 新但未重新构建 → 不得 push 装机。

## 会话恢复协议 —— 每轮对话第一步，不可跳过

无论用户发来什么消息，在回复之前必须先执行：

1. **读取 `.ai-work/STATE.json`**
2. 根据 `current_phase` 和消息类型判断处理：

   | `current_phase` | 收到的消息 | 处理 |
   |---|---|---|
   | `done` | 纯文字 | 正常聊天回复 |
   | `done` | `/auto-code-android-dev` 触发 | **新任务**：从 ENV_CHECK 开始 |
   | `blocked` | 任何消息 | **必须询问用户**："上一任务仍在 blocked。先收尾还是开新任务？" |
   | 其它（非 done/blocked） | **用户反馈 bug/问题/没改好** | ⛔ **禁止直接改代码**。回退到 `planning`，写 `plan-input.md` / `PLAN_PATCH.md`，交 DeepSeek V4 Pro planner 审查，批准后再改 |
   | 其它 | 纯文字补充（非 bug 反馈） | **流程内补充输入**：融入当前阶段，**不得**重新开始 |
   | 其它（非 done/blocked） | `/auto-code-android-dev` 触发 | **必须询问用户**："上一任务在 X 阶段。先收尾还是开新任务？" |

3. 若 STATE.json 不存在：这是首次调用，从 ENV_CHECK 开始
4. **不得自行判断**任务结束或开始新任务
5. **向用户报告**：当前阶段 + 下一步动作

### 用户插话处理

| 用户消息类型 | 处理方式 |
|---|---|
| **反馈 bug/问题/没改好/闪退/UI不对** | ⛔ **禁止直接改代码**。① 写 `plan-input.md` 或 `PLAN_PATCH.md` 描述问题根因 + 修改方案；② 交 DeepSeek V4 Pro planner 审查或生成修订计划；③ planner 批准后才允许改代码。**即使"只改一行"也不得跳过** |
| 补充需求/约束 | 融入 REQUIREMENTS.md，评估是否需要重新分类。若涉及已实现代码的修改，按上条"反馈 bug"处理 |
| 纠正错误理解 | 更新 DECISIONS.md，检查是否影响已完成阶段。若需要改代码，按"反馈 bug"处理——先写方案再审查 |
| 提问当前进度 | 报告 STATE.json 摘要，不中断流程 |
| 要求跳过/加速 | 评估风险，但不得跳过强制门禁 |
| **带 /skill 触发且任务未 done** | **必须询问用户**：先收尾当前任务还是开始新任务 |
| 无关闲聊 | 一句话回复后立即回到流程 |

### `blocked` 状态处理

`current_phase = blocked` 表示任务暂停等待外部条件。主编排 **不得自行 unblock**。

进入条件（参考 `../_shared/SKILL_CORE.md` §2.1）：
- 用户主动说"先暂停/先做别的"（v3 当前就是这个情况）
- 关键依赖不可用（DeepSeek V4 Pro 计划入口不可用）
- 真机验收中用户挂断/出门
- 同一类别编译/测试反复失败 ≥ 3 次
- 关键外部 API 不可用
- Plan Agent 反复 PLAN_GAP 2 次以上

进入 blocked 时：
1. STATE.json 加 `block_reason` 字段
2. 写 `.ai-work/runs/<task>/BLOCKED.md` 记录原因
3. 报告用户

解除 blocked：仅用户明确指令时执行


## Android 默认模型路由

| 角色 | 默认模型 / 工具 |
|---|---|
| 日常主编排 | Claude Code 壳 + MiniMax M3 |
| 计划代理 | DeepSeek V4 Pro |
| 二次计划审查 | Codex；同 Codex 任务可 resume，跨框架用文件交接；无额度时记录延期审查 |
| 开发代理 | MiniMax M3 |
| 测试代理 | MiniMax M3 |
| 高风险增强 | Codex/GPT 有额度时才启用；计划复核在 PLAN_REVIEW 节点，代码审查在 CODE_REVIEW 节点；Codex 无额度时记录并跳过 |

Android 任务在 `PLAN.md` 生成后优先调用 Codex 做二次计划审查；Codex 无额度时记录延期审查，不阻塞当前修复。锁屏、后台服务、权限、生命周期、跨日时间等问题一旦计划错，后续返工成本远高于一次审查。

若 Codex 输出 `changes_required`，不得直接让开发者开改；必须先回到 DeepSeek V4 Pro planner / 计划 owner，由 planner 判断审查意见是否成立并修订 `PLAN.md` / `PLAN_PATCH.md`。Android 的测试靶子、最小复现、logcat 断言和 ADB 验收步骤必须以修订后的计划为准。

## Android 专用差异

### 入口规则

1. 解析 `$ARGUMENTS`
2. 运行 Android 环境检查：
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/auto-code-android-dev/check-environment.ps1" -ProjectRoot "."
   ```
3. 读取 `.ai/ENVIRONMENT_REPORT.md`。Android 环境检查额外验证：
   - `adb` 是否可用
   - `emulator` 与 AVD 是否就绪
   - 当前项目是否为 Android 项目
   - 哪些问题阻塞本 skill，哪些只阻塞模拟器门禁
4. Plan / review / implement 启动规则：
   - Claude Code / Codex 路线：优先通过 `scripts/auto-code-android-dev/run-codex-*.ps1` 启动，禁止用普通后台 Agent 代替正式计划代理。
   - OpenCode + oh-my-openagent 路线：通过 `hyperplan` / `team` / 专用 `run-opencode-*.ps1` 运行；本 Skill 的规则应下沉到 `AGENTS.md` / `.omo/rules/auto-dev.md`，让 OMO 自动注入。
   - 所有路线都必须输出 `status.json`、stdout/stderr 日志路径、最后活动时间、静默秒数和超时状态；超过 600 秒无活动时状态必须显示为 `silent`。

### Android 子智能体

| 智能体 | 职责 | 修改代码 |
|---|---|---|
| `auto-dev-developer` | Android 代码实现，同类别长期开发者 | 是 |
| `auto-dev-tester` | 整类构建、自动化测试、边界场景 | 否 |
| `auto-dev-emulator-tester` | AVD、ADB、安装、Logcat、界面与生命周期验证 | 否 |
| `auto-dev-researcher` | 代码调研、目录分析、调用链梳理 | 否 |
| `auto-dev-brainstorm` / OMO `hyperplan` | 返工诊断、根因分析、计划对抗审查 | 否 |
| `auto-dev-writing` | 文档与提示词整理 | 否 |

### 类别开发

Android 开发额外要求：
- 类别开发前必须先落测试靶子：失败测试、最小复现、日志断言、ADB/界面复现脚本四选一或多选，再写实现
- 每个类别开发完成后，必须通过 ADB 安装到设备/模拟器验证
- 涉及 UI 变更的类别，必须由 `auto-dev-emulator-tester` 执行界面与生命周期验证
- `auto-build-install-after-code-change`：代码变更后自动 `assembleDebug + adb install`

### 测试与验收

Android 测试额外要求：
- 必须有一台可用 Android 设备或 AVD
- `auto-dev-emulator-tester` 负责：安装 APK、Logcat 抓取、界面截图、生命周期测试
- `auto-dev-tester` 负责：单元测试、instrumentation 测试、构建验证
- `DEVICE_TEST_STATUS` 必须有值（`PASSED` / `FAILED` / `SKIPPED`）

### 用户真机实测与同模块追加问题

Android 开发必须承认一个现实：模拟器/自动化测试通过后，用户真机实测可能会发现同模块的连带问题。处理规则：

```text
USER_DEVICE_TEST
  -> USER_ACCEPTANCE_NOTES.md
  -> if same module: FOLLOWUP-<n>.md + original owner repair
  -> if cross module: CATEGORY_DISCOVERY
```

- 用户实测失败或发现同模块新现象时，不默认重新跑完整 `REQUIREMENTS -> RESEARCH -> CATEGORY_DISCOVERY -> PLAN`。
- 同模块问题追加到原类别，由原开发会话继续修，原测试/用户复验链路验证关闭。
- 需要补计划时写 `PLAN_PATCH.md`，并做定点计划审查；不必让首次 planner 从零重写整个 PLAN。
- 只有涉及新模块、公共接口、核心状态机边界变化、权限/后台服务基础逻辑变化时，才重新分类。
- 记录 `USER_DEVICE_TEST_STATUS`：`PASSED` / `FAILED` / `FOLLOWUP_OPENED` / `SKIPPED`。

### 任务恢复

当 `/auto-dev-resume` 被调用时，Android 额外恢复步骤：
- `EMULATOR_TEST` 阶段：恢复原 emulator tester，重新执行安装、Logcat、界面验证
- 恢复前先检查 ADB 设备连接状态

### 相关快捷命令

- `/auto-dev-check` — 检查 auto-dev Skill、Claude 子智能体、Codex CLI、Git 与可选 Android Emulator 环境
- `/auto-dev-resume` — 恢复被中断的 auto-dev 任务，含 EMULATOR_TEST 阶段

## 文件结构

```text
_shared/                              ← 本文件所在目录
├── SKILL_CORE.md                     ← 核心规则 + 阶段路由 + 状态文件 schema
├── WORKFLOW.md                       ← 状态机 + 角色模型 + 并行策略
├── HOOKS.md                          ← 强制门禁定义
├── ROUTING.md                        ← 所有者路由 + 返工升级
├── MODEL_ROUTING.md                  ← 模型路由（默认分工 + 强制规则）
├── REPORT_FORMATS.md                 ← 报告模板
├── WORKTREE_GUIDE.md                 ← worktree 布局
├── skills/                           ← 8 个子阶段 skill（按需读取）
├── templates/                        ← 状态模板
├── scripts/                          ← auto_dev_guard.py
├── auto-dev/SKILL.md                 ← 通用编排入口
└── auto-code-android-dev/SKILL.md    ← 本文件：Android 编排入口
```

未覆盖的规则一律回退到 [`auto-dev`](../auto-dev/SKILL.md) 和 `../_shared/SKILL_CORE.md`。

## OpenCode + oh-my-openagent 使用建议

如果当前 Android 项目主要通过 OpenCode + OMO 执行，不要再强行让 Claude Skill 接管运行时。推荐做法：

1. 把共享核心规则复制/同步到项目根 `AGENTS.md` 和 `.omo/rules/auto-dev.md`。
2. 在 OpenCode 里用：`ultrawork 按 .omo/rules/auto-dev.md 执行本任务`。
3. 涉及多个 Bug 时，先让 Lead/Sisyphus 产出 `CODE_CONTEXT.md` 和 `CATEGORIES.md`，再对每类调用 DeepSeek V4 Pro planner；随后调用 Codex 输出 `PLAN_REVIEW.md`，Codex 无额度则写延期审查记录。
4. Android 真机/模拟器验证仍遵守本文件的 `android_commit_step_gate` 与 `apk_timestamp_check`。
