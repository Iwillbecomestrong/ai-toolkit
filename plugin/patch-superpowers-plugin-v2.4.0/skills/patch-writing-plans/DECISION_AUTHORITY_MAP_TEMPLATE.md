# Decision Authority Map

> 单一业务事实裁决：对同一个业务事实只能保留一套权威判断，下游必须复用其结果，不得再次独立判断。

| Fact ID | Business Fact | Current Authority Location | Output/Decision | Consumers | Change in This Work | User Approval |
|---|---|---|---|---|---|---|

## Rules

1. 下游可以检查结果是否缺失、过期或损坏，但不得重新裁决同一业务事实。
2. 现有权威判断即使不完美，只要不属于本次修复范围，也应保持不变。
3. 若必须改变权威判断、判断条件、结果语义或适用范围，应统一修改原判断及其消费者。
4. 任何上述语义修改都必须先向用户说明当前判断、拟议变化、受影响消费者、用户可见影响和回归风险，并取得用户明确批准。
5. 未批准时状态必须为 `USER_APPROVAL_REQUIRED`，禁止进入实现。
