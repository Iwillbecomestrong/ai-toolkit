---
name: auto-code-android-dev
description: IronWill Android 项目批量开发入口。基于全局 auto-dev 编排框架，增加 Android 专用环境检查、模拟器测试、ADB 验证与 EMULATOR_TEST 阶段恢复。
argument-hint: "<需求、Bug 现象与预期结果>"
disable-model-invocation: true
allowed-tools: Read Write Edit Glob Grep Bash Agent SendMessage
---

# Auto Code Android Dev

用户需求：

$ARGUMENTS

> **基础框架**：本 skill 与 [`auto-dev`](../auto-dev/SKILL.md) 共用 `../` 下的核心文件（SKILL_CORE、WORKFLOW、HOOKS、ROUTING 等）。Android 专用差异仅在本文件定义。

## ⛔ 铁律——禁止跳过（继承自 auto-dev）

以下规则**不可协商**，即使任务看起来"很简单"：
1. **必须走完整流程**：ENV_CHECK → REQUIREMENTS → RESEARCH → CATEGORY_PLANNING → DEVELOPMENT → TESTING → VERIFICATION
2. **不得自行判断"不需要 auto-dev"**。只要通过 /auto-code-android-dev 调用，就必须执行完整流程
3. **PLAN.md 必须由 Codex 子代理生成**。主编排者永远不能自己写 PLAN.md
4. **必须完整阅读 `../SKILL_CORE.md`**
5. **用户中途补充信息 ≠ 退出流程**。即使用户插话补充需求、提问或纠正，流程不会取消。收到任何消息后，第一步永远是读取 STATE.json 恢复状态，从当前阶段继续推进
6. **分类由主编排者亲自做，计划每类独立出**。CATEGORY_DISCOVERY 是编排决策，严禁委托 Codex。BATCH_PLAN_BY_SUBAGENT = 每类一个独立 Codex planner（N 类 = N 次调用），严禁一个 Codex 包揽全部类别

## 会话恢复协议 —— 每轮对话第一步，不可跳过

无论用户发来什么消息，在回复之前必须先执行：

1. **读取 `.ai-work/STATE.json`**
2. 若 STATE.json 存在且 `current_phase` ≠ `done` 且 ≠ `blocked`：
   - 你仍是主编排者，流程未完成
   - 用户的消息是流程中的补充输入，不是"新任务"
   - 从 `current_phase` 继续推进，**不得**重新开始、**不得**退回
3. 若 STATE.json 不存在：这是首次调用，从 ENV_CHECK 开始
4. 若 `current_phase` = `blocked`：向用户报告阻塞原因
5. 若 `current_phase` = `done`：流程已完成，正常回复
6. **向用户报告**：当前阶段 + 下一步动作

### 用户插话处理

| 用户消息类型 | 处理方式 |
|---|---|
| 补充需求/约束 | 融入 REQUIREMENTS.md，评估是否需要重新分类 |
| 纠正错误理解 | 更新 DECISIONS.md，检查是否影响已完成阶段 |
| 提问当前进度 | 报告 STATE.json 摘要，不中断流程 |
| 要求跳过/加速 | 评估风险，但不得跳过强制门禁 |
| 无关闲聊 | 一句话回复后立即回到流程 |

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
4. Codex plan / review / implement **只能**通过 `scripts/auto-code-android-dev/run-codex-*.ps1` 启动。禁止用 `Agent`、`SendMessage` 或其他后台子任务代替 Codex B/C。`run-codex-*.ps1` 默认以前台方式运行，在当前 shell 持续输出运行日志；同时必须把生成的 `status.json`、stdout/stderr 日志路径回显给用户；超过 600 秒无活动时状态必须显示为 `silent`。

### Android 子智能体

| 智能体 | 职责 | 修改代码 |
|---|---|---|
| `auto-dev-developer` | Android 代码实现，同类别长期开发者 | 是 |
| `auto-dev-tester` | 整类构建、自动化测试、边界场景 | 否 |
| `auto-dev-emulator-tester` | AVD、ADB、安装、Logcat、界面与生命周期验证 | 否 |
| `auto-dev-researcher` | 代码调研、目录分析、调用链梳理 | 否 |
| `auto-dev-brainstorm` | 返工诊断、根因分析 | 否 |
| `auto-dev-writing` | 文档与提示词整理 | 否 |

### 类别开发

Android 开发额外要求：
- 每个类别开发完成后，必须通过 ADB 安装到设备/模拟器验证
- 涉及 UI 变更的类别，必须由 `auto-dev-emulator-tester` 执行界面与生命周期验证
- `auto-build-install-after-code-change`：代码变更后自动 `assembleDebug + adb install`

### 测试与验收

Android 测试额外要求：
- 必须有一台可用 Android 设备或 AVD
- `auto-dev-emulator-tester` 负责：安装 APK、Logcat 抓取、界面截图、生命周期测试
- `auto-dev-tester` 负责：单元测试、instrumentation 测试、构建验证
- `DEVICE_TEST_STATUS` 必须有值（`PASSED` / `FAILED` / `SKIPPED`）

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
├── REPORT_FORMATS.md                 ← 报告模板
├── WORKTREE_GUIDE.md                 ← worktree 布局
├── skills/                           ← 8 个子阶段 skill（按需读取）
├── templates/                        ← 状态模板
├── scripts/                          ← auto_dev_guard.py
├── auto-dev/SKILL.md                 ← 通用编排入口
└── auto-code-android-dev/SKILL.md    ← 本文件：Android 编排入口
```

未覆盖的规则一律回退到 [`auto-dev`](../auto-dev/SKILL.md) 和 `../SKILL_CORE.md`。
