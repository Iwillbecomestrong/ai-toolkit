# Input Source Classification

## MUST_FOLLOW
| ID | 路径/来源 | 约束范围 | 必须遵守内容 | 读取状态 | 冲突状态 |
|---|---|---|---|---|---|
| MF-001 |  |  |  | `NOT_READ | READ_AND_APPLIED` | `NONE | USER_DECISION_REQUIRED` |

## CONFIRMED_FACTS
| ID | 事实 | 证据等级 | 证据路径 | 确认人/时间 |
|---|---|---|---|---|

## UNKNOWN
| ID | 未知问题 | `LOAD_BEARING | NON_LOAD_BEARING` | 所需证据 | Owner | Status |
|---|---|---|---|---|---|

## REFERENCE_ONLY_PATHS
| ID | 路径 | 主题 | 来源 | 读取状态 | Access Request |
|---|---|---|---|---|---|
| REF-001 |  |  |  | `NOT_READ` | `NONE` |

> `REFERENCE_ONLY_PATHS` 只记录路径，不复制内容；默认不得读取。
