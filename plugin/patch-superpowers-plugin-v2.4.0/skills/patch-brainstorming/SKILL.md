---
name: patch-brainstorming
description: Use when a software feature, bug fix, refactor, or behavior change needs requirements clarification, source classification, evidence boundaries, and user-approved design before planning.
---

# Patch Brainstorming：输入分类与设计

先理解目标、项目现状和成功标准，再提出 2–3 个方向并获得用户批准。进入计划前必须生成 `INPUT_CLASSIFICATION.md`，固定分为：

1. `MUST_FOLLOW`：用户指定必须遵守的文件、决定、不变量和验收；必须完整读取、逐项覆盖。冲突时停止并询问用户。
2. `CONFIRMED_FACTS`：已由代码调用链、数据/状态流、测试、日志、真机或用户明确确认的事实。
3. `UNKNOWN`：尚未确认的问题；标记是否承重及关闭证据。
4. `REFERENCE_ONLY_PATHS`：仅记录路径、主题和来源，默认状态 `NOT_READ`。

## 延迟参考规则

`REFERENCE_ONLY_PATHS` 默认不得读取。正确顺序：

```text
读取 MUST_FOLLOW
→ 先调查代码、调用链、状态流、日志、测试和真实行为
→ 尝试仅根据确认事实推导解决方案
→ 确实无法形成可行方案时，才提交 REFERENCE_ACCESS_REQUIRED
→ 只读取申请的具体 Reference ID
→ 将其中技术声明标记为 UNVERIFIED_REFERENCE
→ 经代码分析、逻辑验证、测试或验证性小实验后，才能转为 CONFIRMED 并进入计划
```

不得把参考文件正文复制进头脑风暴产物。不得因为“历史上讨论过”就先读参考答案。

## 产物

- `INPUT_CLASSIFICATION.md`
- `MUST_FOLLOW_INDEX.md`
- `SPEC.md`：只写问题、行为、不变量、范围和证据等级，不写具体解法
- `BRAINSTORM_DESIGN.md`

用户批准设计后，转入 `patch-superpowers:patch-writing-plans`。
