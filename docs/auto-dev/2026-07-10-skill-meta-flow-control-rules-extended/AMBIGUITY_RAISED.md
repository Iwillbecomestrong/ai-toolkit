# AMBIGUITY_RAISED — planner 发现的不明确项

> 按 §0.11.1 case B protocol：planner 发现 ambiguity 后通过本文件回报，主编排代问用户。

---

## A-1: `_shared/SKILL.md` 不存在 -- Q-11 命名规则引用目标缺失

**触发**: 任务描述要求列 `ai-toolkit/skills/_shared/SKILL.md` 为 files_in_scope（Q-11 命名规则引用），但该文件在 `_shared/` 目录下不存在。

**实际存在的文件**:
- `G:\ai-toolkit\skills\_shared\SKILL_CORE.md`（存在）
- `G:\ai-toolkit\skills\_shared\WORKFLOW.md`（存在）
- `G:\ai-toolkit\skills\_shared\MODEL_ROUTING.md`（存在）
- `G:\ai-toolkit\skills\_shared\SKILL.md`（**不存在**）
- `G:\ai-toolkit\skills\auto-dev\SKILL.md`（存在，是 auto-dev 的薄入口）

**planner 临时决策**: 
- Q-11 命名规则的主体内容落在 `SKILL_CORE.md` §0.11（新增命名规则段）
- 引用侧改为 `auto-dev/SKILL.md`（实际存在的 SKILL.md 入口文件），在 PLAN 中标记此替换
- files_in_scope 中 `_shared/SKILL.md` 替换为 `auto-dev/SKILL.md`

**需要用户确认**:
- 是否接受将 `_shared/SKILL.md` 替换为 `auto-dev/SKILL.md` 作为 Q-11 命名规则的引用落地文件？
- 还是需要新建 `_shared/SKILL.md`？

---

## A-2: C-6 "Q-13 session 复用 cache 跨 model 落地机制" 仍为 Open Q

**触发**: USER_NEEDS_DIGEST.md §C-6 标记为"Open Q"。Codex (OpenAI) 和 DeepSeek (via litellm) 是两个不同 model provider，各自维护 cache。

**当前 PLAN 处理**: 按 C-6 所述落地方式 -- subagent dispatch 时填 `sub_session_id = <pipeline_id>`，所有 sub-agent 用同一 `<pipeline_id>`。实际 cache 命中率由各 provider 内部决定，主编排不负责 guarantee cross-model cache hit。

**需要用户确认**: 是否认可此落地方式？

---

## A-3: Q-11 "长而清命名" 的最长长度未量化

**触发**: USER_NEEDS_DIGEST.md §C-4 标记"Q-11 命名规则 '长' 多长"为未澄清。

**当前 PLAN 处理**: 规则写"采用几个英文单词全程或中文，禁用缩写"，但不设硬性字符上限。开发阶段由 developer 按此原则执行，reviewer 阶段检查。

**需要用户确认**: 是否需要硬性字符数上限？还是接受"几个英文单词全程或中文"作为充分约束？

---

**END OF AMBIGUITY_RAISED.md**
