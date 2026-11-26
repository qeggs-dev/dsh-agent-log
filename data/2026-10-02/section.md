<!-- 20261002-005 -->

## 待办（修复目标已于 2026-10-02 选定并交付，仅…

待办（**修复目标已于 2026-10-02 选定并交付**，仅剩上游代码修复未做）：DSH 事件循环卡死走「外部预付费」路线，工具在工作区 `dsh-stall-monitor\prepay-acl.ps1|.cmd|.mjs`——用桌面版自带的 `AclWriteGrant` + `workspaceWriteSid`，在 **DSH 之外**做与宿主 `materializeAclGrant` 完全相同的 grant（`grant.add(path, true)`），把几十秒的全树传播移出事件循环；

带自检（首遍慢则自动再跑一遍，第二遍仍慢即报 FAIL 并列出所需 ACE 形状），并追加写 `prepay-acl.log`。实测对 `〈项目目录〉/QQBot` / 本工作区各 **19 ms / 3 ms** 返回（跳过分支、零传播），二者此后不再卡。

### 仍未做

把工作区根的 grant 挪进 runner 进程的源码修复——落点是 `dsh-sandbox-windows-acl/lib/runner.js:149` 的 `manageDacls: !seamManaged`，让它也承担工作区 grant（runner 本就是独立进程，且 `AclSandbox` 构造器已支持对 `writableDirs` 逐个 `grantWrite`，`confine()` 的同步契约不受影响）；

改哪里（checkout `〈源码目录〉/deepseek-harness` 是 0.1.0-rc.5、缺 deny/Low 标签所以修不到在跑的桌面版 / 改桌面版 app.asar 能修到但升级即失效 / 只写文档）尚未决定，checkout 的依赖与构建健康度（能否 `pnpm dsh web`）未验证
