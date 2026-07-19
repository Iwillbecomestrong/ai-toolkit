# Planning Contract

1. MUST_FOLLOW 文件必须完整读取并在 Core Plan 中逐项覆盖。
2. Spec 只冻结问题，不冻结实现方案。
3. REFERENCE_ONLY 默认 NOT_READ；先调查代码与真实行为。
4. 仅在 `REFERENCE_ACCESS_REQUIRED` 获准后定点读取参考路径。
5. 参考技术声明初始为 UNVERIFIED_REFERENCE；只有 CONFIRMED 可进入计划。
6. 存在未关闭承重假设时禁止冻结 Core Plan。
7. 同一业务事实只能有一个权威判断；下游不得重新裁决。
8. 修改权威判断必须取得用户明确批准。
9. Core Plan 先经 Claude 对抗审查和用户批准，才展开详细计划。
10. 详细计划不得改变已批准 Core Plan；改变时回退重审。
11. 真实环境需求不得由静态代码或单测降级替代。
12. 测试绿不等于行为正确，必须验证正向、负向与功能存活。
