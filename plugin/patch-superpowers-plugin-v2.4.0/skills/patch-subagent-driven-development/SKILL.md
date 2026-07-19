---
name: patch-subagent-driven-development
description: Use when an approved Patch Superpowers detailed DAG should be executed in the current Claude session with fresh Claude implementers and Codex Luna reviewers.
---

# Patch Subagent-Driven Development

必须先通过 `patch-superpowers:patch-dag-worktree-development` 的入口门禁。每个 Execution Task 使用一个责任 Claude Agent、一个 worktree/branch、完整 TDD 和一次独立 Luna Review。按依赖动态计算 READY；不使用 Wave 或 Cluster。
