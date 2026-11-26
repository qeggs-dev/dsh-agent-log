<!-- 20261002-002 -->

## 0.1.0-rc.5 → 0.2.0-rc.2 的 `grantWrite` 幂等跳过条件收紧了，这是卡死"该只付一次却付了"的直接原因

旧版只检查「能力 SID 的 Allow ACE（mask 0x00110156、OI|CI）」且只写 DACL；

新版要求**三条同时成立**（①能力 Allow ACE ②Everyone 的 Deny ACE，mask=0x40、仅 CI ③Low 完整性标签，type=17、inh=3、mask=1、S-1-16-4096），并把三者塞进**同一次** `SetNamedSecurityInfoW`（security info = 4 或 20）。

故**任何被旧版授权过的根，在新版下的第一次 grant 必然不跳过、必然重付一次全树传播**；源码注释自陈 "a root granted by an earlier build receives the deny on its next provision"。

`D:\Projects\QQBot`（230,264 文件）与本工作区**均已付完**，三条条件经 `Get-Acl` 实测全部成立，此后走 O(1) 跳过

<!-- 20261002-003 -->

## 本机 NTFS 上「以可写方式打开文件再关闭」**不会**更新…

本机 NTFS 上「以可写方式打开文件再关闭」**不会**更新 LastWriteTime（实测 `FileAccess::ReadWrite` + `FileShare::ReadWrite` 的 open/close 前后时间戳完全相同，只读方式同样不变），只有真正写入数据才会。

因此 `D:\Deepseek_Harness_Temp\dsh-acl-locks\*.lock` 的 mtime **恒等于其创建时间**，可用来读「DSH 第一次保护该路径的时刻」（QQBot=2026-09-23 15:05:11，本工作区=2026-09-17 23:17:42），但**不能**用来判断"是否发生过 DACL 写"。

据此，此前"锁目录无写入 ⇒ 那个时段没有 ACL 操作"的推理已作废，相关结论已从 `dsh-stall-monitor\FINDINGS.md` 撤回

<!-- 20261002-006 -->

## 工作区 `dsh-stall-monitor\` 现在同时是**…

工作区 `dsh-stall-monitor\` 现在同时是**证据库**与**修复工具集**：`FINDINGS.md` 是权威记录（第 0 节根因 + 三条跳过判据 + 调用频率 + 修复落点，第 1.4 节是被实测推翻并已作废的旧推理，第 四 节是方案对照）；

`asar-extract\` 是从 `app.asar` 抠出的**运行版 0.2.0-rc.2** sandbox 源码（`dsh-sandbox-windows-acl` / `dsh-sandbox-local` / `dsh-pwsh-sandbox` 等，行号可直接引用；

checkout 是 0.1.0-rc.5，两者行为不同，看代码务必认准这一份）；`prepay-acl.*` 是修复工具。

### 任务结束后待清理

2 份 507 MB full dump + 2 份 6.5 MB mini dump、旧 `out-*` 数据目录、`.venv-monitor\` 空壳

<!-- 20261002-010 -->

## 新增桌面版预设**讨论模式**（config.id `discu…

新增桌面版预设**讨论模式**（config.id `discuss`，patch 行 id `preset-discuss`，order 15），与**协作模式**成对：**工具集与 collab 逐行完全相同**（19 个顶层行，代码级比对 IDENTICAL），差别全在 persona——默认把工作区当作**要讨论的材料**（数据 / 文档 / 笔记 / 日志）而非待办的项目，先读再谈、把内容讲清就是交付，发现材料里的错值 / 不一致只报告不改；

任何留痕动作（含"顺手改"）都要先拿授权，未授权时写操作一律先给方案再等确认。

persona 源文件为工作区 `dsh-desktop-presets\personas\discuss.txt`（4350 字符），live 树里 `include:preset-discuss` 已 schema-validated 且 HMR 热生效、无需重启

<!-- 20261002-011 -->

## `generate.mjs --append` 曾会静默删掉 profile patch 尾部的 `- id: agent-preset-registry`

（原来从 marker 一路 `slice` 到文件末尾），后果是预设都还在、但 `default: standard` / `selectedDefault: collab` 被一起抹掉且不报错。

### 已修

生成段只延伸到「marker 之后第一个顶格且非 `- insert:` 的顶层条目」为止，其后内容原样保留（本次实测保留了 6 行）；

`dsh-desktop-presets\tests\append-logic.test.mjs` 是纯文本回归测试，断言尾部逐字保留 / 7 个预设行齐全 / 幂等 / `selectedDefault` 仍在，**改动该脚本前先跑它**
