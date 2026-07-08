# OpenCode + oh-my-openagent 桥接说明

你现在如果固定使用 OpenCode + oh-my-openagent，本 Skill 不应该继续只作为 Claude Code 的 `/auto-dev` 入口存在。更好的做法是：

1. `01-auto-dev-SKILL.md` 等文件继续作为 Claude/Codex 场景的完整 Skill。
2. OpenCode/OMO 场景，把规则下沉到：
   - 项目根 `AGENTS.md`
   - `.omo/rules/auto-dev.md`（通用流程）
   - `.omo/rules/auto-code-android-dev.md`（Android 专用扩展，按需加载）
3. 让 oh-my-openagent 的 rules injection 自动加载你的流程规则。

本打包目录已经给出可直接复制的桥接文件：

```text
opencode-omo-bridge/
├── AGENTS.md
└── .omo/rules/
    ├── auto-dev.md
    └── auto-code-android-dev.md
```

## 推荐用法

在你的项目根执行：

```bash
mkdir -p .omo/rules
cp opencode-omo-bridge/AGENTS.md ./AGENTS.md
cp opencode-omo-bridge/.omo/rules/auto-dev.md ./.omo/rules/auto-dev.md
cp opencode-omo-bridge/.omo/rules/auto-code-android-dev.md ./.omo/rules/auto-code-android-dev.md
```

然后在 OpenCode 里发任务时这样说：

```text
ultrawork 按 .omo/rules/auto-dev.md 执行：先调研、分类、每类独立计划，计划批准后再开发。不要跳过测试和工作树卫生。

如果是 Android / IronWill 任务，再补一句：额外遵守 .omo/rules/auto-code-android-dev.md 的 Gradle、ADB、APK、Logcat 和真机/模拟器验收规则。
```

复杂任务建议先用：

```text
hyperplan 根据 .omo/rules/auto-dev.md 审查这个任务计划，只输出风险、分类、依赖和验收标准，不要改代码。
```

## 这版的定位

- Claude：适合做主编排、意图判断、类别划分、返工归因。
- DeepSeek V4 Pro：默认负责计划、定点分析和普通高风险分析。Codex：负责二次计划审查和关键代码审查。
- MiniMax M3：默认负责开发、测试、日常执行和低成本多路推进。
- OpenCode + OMO：适合长时间执行、Team Mode 并行、LSP/AST-Grep 辅助、ulw-loop 持久推进。
- Codex：有额度时负责二次计划审查和关键代码审查；无额度时记录 CODEX_STATUS.json / DEFERRED_CODEX_REVIEW.md 并跳过（仅审计追溯，不自动补跑）。GPT：只在有额度时作为更高风险增强。

不要再引入 Reasonix，减少路线分叉。
