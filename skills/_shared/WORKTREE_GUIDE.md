# Shared Worktree Guide — auto-dev / multi-agent-core

## Goal

并行的是"不同类别"，不是多个代理同时改同一个工作目录。

## Rules

1. 最大并行类别数为 3。
2. 每个并行类别必须有独立 worktree。
3. 每个并行类别必须有独立 branch。
4. 每个并行类别必须有独立 developer / tester 责任身份。
5. 每个 wave 单独建立 integration worktree。

## Suggested Layout

```text
<project-parent>/
├─ main-repo/
├─ worktrees/
│  ├─ category-a/
│  ├─ category-b/
│  ├─ category-c/
│  └─ integration-wave-1/
└─ {STATE_DIR}/
   ├─ STATE.json
   ├─ ISSUES.json
   ├─ waves/
   └─ runs/
```

## Integration Order

```text
merge category A
-> quick integration check
merge category B
-> quick integration check
merge category C
-> wave integration test
```

## Debug Read Order

1. 先看失败测试、错误日志、冲突文件、修改文件清单、提交哈希。
2. 单类问题只读单类文档。
3. 双类冲突只读两类文档。
4. 真正三方问题才读三类文档。
