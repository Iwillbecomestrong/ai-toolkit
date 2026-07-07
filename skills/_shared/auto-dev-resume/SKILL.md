---
name: auto-dev-resume
description: 恢复被中断的 auto-dev 任务，读取状态、原子智能体 ID 和已有报告后从正确阶段继续。
argument-hint: "[任务目录；省略则选最新任务]"
disable-model-invocation: true
allowed-tools: Read Write Edit Glob Grep Bash Agent SendMessage
---

# 恢复 Auto Dev

目标任务：$ARGUMENTS

1. 若未提供目录，从 `.ai/tasks/` 选择修改时间最新且非 `COMPLETED` 的任务。
2. 读取任务目录的 `STATUS.md`、`CURRENT_CODEX_RUN.json`（若存在）、`AGENT_STATE.md`、`BUGS.md` 和当前阶段报告。
3. 若 `CURRENT_CODEX_RUN.json` 指向的 `status.json` 仍显示 `running` / `silent`，先据此确认最近一次 Codex 规划或审查卡在哪个阶段，再决定是续跑、等待还是重启。
4. 检查 Git 工作树与任务记录的 base commit，发现外部修改时先记录，不覆盖。
5. 按 `current_stage` 恢复：
   - `PLAN`：重新执行 Codex 规划。
   - `DEVELOP` 或产品 Bug：用 `SendMessage` 恢复原 developer ID；若原 ID 不可恢复，生成新 developer，并把原因写入状态。
   - `TEST`：恢复原 tester。
   - `EMULATOR_TEST`：恢复原 emulator tester。
   - `REVIEW`：运行新的 Codex 审核。
6. 后续严格遵循 `../auto-code-android-dev/SKILL.md` 的门禁，并继承 `../` 下的通用规则（SKILL_CORE、WORKFLOW、HOOKS、ROUTING 等）、返工上限和完成条件。
7. 不因恢复任务而跳过已经失效的测试；若代码自上次报告后变化，重新执行受影响测试。
