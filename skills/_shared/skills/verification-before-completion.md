# Verification Before Completion

任何代理不得仅凭"应该已经好了"宣布完成。

类别关闭前至少记录：

- `VERIFIED_COMMIT`
- `VERIFICATION_COMMAND`
- `VERIFICATION_TIME`
- `EXIT_CODE`
- `RESULT_FILE`
- `DEVICE_TEST_STATUS`
- `REMAINING_RISKS`

必须确认验证针对的是最终提交，而不是修复前版本。

设备不可用时，必须显式区分：

- 已完成的代码验证
- 尚未完成的设备验证
- 当前无法排除的风险

提交前 → `pre_commit_gate` 钩子。任务完成 → `post_task_reflection` 钩子。
