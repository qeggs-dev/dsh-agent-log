<!-- 20261126-003 -->

## diff-edit 0.2.0：新增 `patch_diff` 工具与 `diffEdit` 服务（2026-11-26）

用户要求「传入一个 diff 文件按文件应用修改，支持 reverse 反向 patch」，以及「新增插件接口让其它插件传入两个文件生成 diff 文件、并应用 diff 更改（或反向，传入 diff 字符串）」。

### patch_diff 工具

`description`、`patch_file`、`reverse`、`strip`、`dry_run`。路径取自 patch 头（优先 `+++`；`/dev/null` 表示新建/删除），相对会话工作目录；

`strip` 类似 `patch -p`，省略时自动识别 git 的 `a/`+`b/`（自动 1）与无前缀（0）。**先整单预检**（逐文件读内容、逐个 hunk 内存应用、检查可写根）任一不符则不写；**按顺序写、失败回滚已更新的文件**（新建的文件无法删除会留在原地并报告，本插件从不删文件）。

拒绝删除、rename/copy、二进制 patch；`/dev/null`、时间戳后缀、git 引号路径（含八进制字节，中文文件名）都能解析；email-format patch 明确拒绝。反向用 jsdiff `reversePatch` 生成逆 hunk 再 `applyPatch`。

### diffEdit 服务

`ctx.provide('diffEdit')`：`createDiff({oldPath,newPath,diffFile?,oldName?,newName?,context?})` 生成统一 diff 并可落盘（一侧缺失生成 /dev/null 的新建或删除 diff，相同则 `changed:false` 不写文件）；

`applyDiff({patch,reverse?,dryRun?,strip?})` 应用 diff 字符串；`reverseDiff({patch})` 返回逆 diff 文本不碰文件。

都可选 `{cwd,session,agent,signal}`：`session` 决定沙箱、`agent` 接 harness 写入守卫、没有 agent 时用自己读到的版本做 `replaceIfVersion` CAS；只读会话拒绝写入（dryRun 允许）。

### 验证

`tests/apply.test.mjs` 50 条纯逻辑 + `tests/service.test.mjs` 20 条 Host 级（假 ctx + 真临时目录）全过；

live e2e 通过（两文件 git patch、reverse 还原、创建文件、删除被拒、dry_run 不落盘、strip 自动/显式、错误信息带路径）；

`plugin_manager list_plugins` 显示 `@local/diff-edit` 为 enabled/active，说明 `apply`（含 provide）完成。

### 注意

插件自己 provide 的服务**不出现在 `cordis_inspect_query` 的 Service 目录里**（`libCache`、`pyserver` 同样不在），别用它验证 provide；

安装插件改代码不热加载（R-059），本次两次 `restart_dsh` 才让 `patch_diff` 与修好的文案生效。

### 关键代码

`lib/diff-apply.js` 新增 `splitPatchSections`、`pathFromHeaderLine`/`unquoteGitPath`、`detectStrip`、`stripPatchPath`、`reverseHunks`、`createPatchText`、`countDiffChanges`，`parseUnifiedDiff` 增加 `lineOffset`（patch 文件里按整文件行号报错）；

`index.js` 新增 `planPatchFile`/`commitPatchPlan`（预检与回滚）、`patchValueOf`、`createDiffService`。提交 `7435288`（功能）与 `47949b1`（错误信息带目标路径 + 行号偏移）。README 已写全两个工具与服务用法。
