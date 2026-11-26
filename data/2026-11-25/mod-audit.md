<!-- 20261125-013 -->

## mod-audit 拖包后只显示根节点并报 “Function…

mod-audit 拖包后只显示根节点并报 “Function object could not be cloned” 的根因：analyzer.js 在每个 mod 上挂 mod.reopen = j.getBytes（重读 jar 的函数），而 worker.js 把 mod 与 res.mods 直接 postMessage 到主线程，函数无法结构化克隆 → DataCloneError → collect() 中断，界面只画根节点。修复：worker.js 新增 cloneable() 递归丢弃函数字段（含 typeof v 为 function 的早退分支——最初漏了这一支，导致净化后仍带函数），done 消息里的 errors 也转纯对象；主线程 done 分支仍按文件名回挂 reopen。端到端验证（Electron + 3 个真实 jar）：4/4 节点（1 根 + 3 mod）、61 条常量、4 个注入点，无报错。提交 fbaafd1，2026-11-25 已推送 origin/main。
