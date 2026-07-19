# Patch Superpowers Plugin v2.4.0 Test Results

## 结论

- Python 测试：13 passed
- 包结构验证：VERIFY_OK
- Python 脚本编译：通过
- Codex 显式模型命令构造：通过
- 等价持久安装与旧 Overlay 清理模拟：通过
- 原 Superpowers 四个代表性 Skill 保留：通过
- Hooks：NONE（设计决定）

## 关键验证

### 模型路由

- Core Planner：`gpt-5.6-sol + medium`
- Detailed Planner：恢复原 Sol thread，仍显式 `gpt-5.6-sol + medium`
- Task Reviewer：`gpt-5.6-luna + medium`
- Integration Reviewer：`gpt-5.6-luna + medium`

### 输入与参考门禁

- `MUST_FOLLOW / CONFIRMED_FACTS / UNKNOWN / REFERENCE_ONLY_PATHS` 四类齐全；
- Reference 默认 `NOT_READ`；
- 只有 `REFERENCE_ACCESS_REQUIRED` 获准后才能定点读取；
- `UNVERIFIED_REFERENCE` 不能进入计划；
- 只有 `CONFIRMED` 参考声明可被 Core Plan 使用；
- 未关闭承重假设、未批准权威判断变化和未批准详细计划均阻止执行。

### 安装模拟

在临时 Claude Home 中：

- 安装到 `.claude/skills/patch-superpowers`；
- 删除 5 个明确属于旧 Overlay 的独有目录；
- 保留原版 `brainstorming`、`writing-plans`、`using-superpowers`、`subagent-driven-development`；
- 安装后重新运行 `Verify-Package.py` 通过。

## 未执行的真实验证

当前构建环境没有 `claude`、`codex` 和 PowerShell，因此未执行：

- `claude plugin validate . --strict`；
- `claude --plugin-dir <zip>` 的真实加载；
- `/reload-plugins` 后的 Skill/Agent UI 发现；
- 真实 Codex 模型调用；
- `Install.ps1` 的 PowerShell 运行。

以上限制不能由静态测试替代，安装包中的 `INSTALL_BY_AI.md` 要求本地安装 AI 补做这些验证并如实报告。
