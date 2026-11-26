<!-- 20261123-001 -->

## DSH-SSH 的 ssh_fork 不再把已存凭据发给页面（2…

DSH-SSH 的 ssh_fork 不再把已存凭据发给页面（2026-11-23 用户决定）：GET /dsh-ssh/pending 只返回源条目 id 与认证方式，弹窗凭据栏显示「复用源的身份凭证」；密码或密钥路径留空即由 Host 在连接时从凭据库读取源条目的凭据，填了则覆盖。

### 原因

明文预填让任何本机进程（含探测脚本）都能读到密码，违背「模型/页面永远看不到凭据」。实现见 dsh_plugins/dsh-ssh 提交 2b3985e。

<!-- 20261123-005 -->

## DSH-SSH 的 ssh_shell 变量参数 vars（20…

DSH-SSH 的 ssh_shell 变量参数 vars（2026-11-23 用户两次要求定型）：结构是**字典**，变量名 → 模式，模式枚举 `value` / `template`。

`value`：值拼成 `export NAME='…'` 放在命令前，由远端 shell 展开（引号由插件负责，子进程可见，写在单引号里不展开）。`template`：发送前把 `$NAME`/`${NAME}` 直接替换成值（长名字优先），因此单引号里也生效，且**不做任何转义**，周围引号由 Agent 负责。

### 流程

审批卡 →（卡上写 `NAME (mode)`）→ 变量弹窗：左侧命令预览高亮当前变量、右侧变量名 + 模式标签「远端展开 / 先展开再发送」+ 一行说明 + 多行输入，chips 可切换，Ctrl+Enter 运行，Esc/拒绝 = 不执行。

值不回模型（结果只有变量名 + redacted 计数）、不进审计、回声按整值精确替换成 [redacted]；不能与 background:true 同用；远端 ps 可见。提交 876b98d。实测 Ubuntu 真机：value 模式 `wc -c` = 17；

template 模式 `echo 'n=$NOTE'` → `n=[redacted]`；DOM 读到两段标签「远端展开」「先展开再发送」。
