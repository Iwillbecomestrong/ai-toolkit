# Skill Versioning — Git Worktree 管理规范

> 适用于 auto-dev、multi-agent-core 及所有需要自我迭代的 Skill。

## 1. 核心原则

- **current 是只读的**：正在被任务使用的版本，不得直接修改
- **修改必须通过 change worktree**：每次修改独立一个 worktree
- **合并走 next → current**：多个 change 先合并到 next，验证后发布为 current
- **所有变化 Git 可追踪**

## 2. 目录结构

```
skills/<skill-name>/
├── current/                          # 当前稳定版（只读）
├── next/                             # 下一版整合区
├── changes/                          # 修改 worktree
│   ├── <skill>-change-YYYYMMDD-功能名/
│   ├── <skill>-fix-YYYYMMDD-问题名/
│   └── <skill>-hook-YYYYMMDD-门禁名/
├── archive/                          # 已合并的 worktree
└── registry/
    └── skill-change-registry.json    # 修改登记表
```

## 3. 命名规则

### 当前正式版

```
<skill>-current
<skill>-release-v1.4.2          # 严格版本管理
```

### 下一版整合区

```
<skill>-next-v1.5.0
```

### 修改 worktree

| 类型 | 命名 | 示例 |
|---|---|---|
| 新增功能 | `<skill>-change-YYYYMMDD-功能名` | `auto-dev-change-20260706-post-task-learning` |
| 修复流程 | `<skill>-fix-YYYYMMDD-问题名` | `auto-dev-fix-20260706-no-plan-direct-edit` |
| Hook 门禁 | `<skill>-hook-YYYYMMDD-门禁名` | `auto-dev-hook-20260706-plan-required-before-edit` |
| 模板调整 | `<skill>-template-YYYYMMDD-模板名` | `auto-dev-template-20260706-verification-report` |
| 紧急修复 | `<skill>-hotfix-YYYYMMDD-问题名` | `auto-dev-hotfix-20260706-commit-without-verification` |

## 4. 每个 change worktree 必须包含

```
<skill>-change-YYYYMMDD-xxx/
├── SKILL_CHANGE.md           # 修改说明
├── CHANGE_MANIFEST.json      # 结构化 manifest
└── TEST_REPORT.md            # 验证报告（合并前）
```

### SKILL_CHANGE.md 模板

```markdown
# Skill 修改说明

CHANGE_NAME:
SOURCE_SESSION:
SOURCE_TASK:
BASE_SKILL_VERSION:
BASE_COMMIT:

## 为什么要改
## 改了什么
## 新增了什么功能
## 影响范围
## 风险
RISK: LOW | MEDIUM | HIGH
## 是否建议合并
MERGE_RECOMMENDATION: YES | NO | NEED_USER_REVIEW
## 合并前需要验证
```

### CHANGE_MANIFEST.json 模板

```json
{
  "change_id": "",
  "change_type": "hook_feature | bug_fix | refactor | template",
  "source_session": "",
  "source_task": "",
  "base_skill_version": "",
  "base_commit": "",
  "created_at": "",
  "purpose": "",
  "changed_files": [],
  "added_features": [],
  "risk": "LOW | MEDIUM | HIGH",
  "status": "pending_merge | merged | rejected | deferred | duplicate",
  "merge_target": ""
}
```

## 5. 修改流程

```
发现 Skill 问题
  → 创建 <skill>-change-YYYYMMDD-xxx worktree
  → 在 worktree 中修改
  → 写 SKILL_CHANGE.md
  → 写 CHANGE_MANIFEST.json
  → 测试验证
  → 提交到 change branch
  → 等待合并
```

## 6. 合并流程

```
多个 change worktree 完成
  → 读取每个 SKILL_CHANGE.md
  → 去重
  → 解决冲突
  → 合并到 <skill>-next-vX.Y.Z
  → 运行 Skill / Hook 验证
  → 更新 CHANGELOG.md
  → 打版本号
  → 发布为 <skill>-current
```

合并后标记状态：
- `merged` — 已合并
- `duplicate` — 重复
- `rejected` — 不采纳
- `deferred` — 延后

## 7. 任务完成后的沉淀

```
任务完成
  → 写 AUTO_DEV_LEARNINGS.md
  → 检查是否有值得改 Skill 的内容
  → 有 → 创建 change worktree
  → 无 → 结束
```

**禁止直接修改 current。**

## 8. 升级 current 的条件

- next 已合并完候选修改
- Hook 测试通过
- Skill 流程测试通过
- CHANGELOG 已更新
- VERSION 已更新
- 当前无阻塞的活跃任务
- 用户确认

## 9. 注册表

`skill-change-registry.json` 记录所有 change 的状态：

```json
{
  "skill": "auto-dev",
  "changes": [
    {
      "change_id": "auto-dev-change-20260706-shared-core-hooks",
      "status": "in_progress",
      "created_at": "2026-07-06",
      "merged_at": null,
      "merge_target": "auto-dev-next-v1.0.0"
    }
  ]
}
```
