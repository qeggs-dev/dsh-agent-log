<!-- 20261128-008 -->

## Lua 指令预算实测（2026-11-28，LuaJ 3.0.1）

debug.sethook(f,空串,N) 能掐断 while true do end（error 让 resume 返回 false），但钩子不会继承到新建协程——主线程装钩、脚本自己 coroutine.create 的死循环会真的卡死（4 秒看门狗才退出）；必须在协程自己的线程里装钩才有效。

### 结论

嵌入 Lua 必须加固 coroutine.create/wrap（新协程启动先装预算钩子），且不把 debug 暴露给脚本，否则 Lua 能卡死服务器这一条不成立。wasmoon（Lua 5.4 wasm）按同一思路，mcbot 用每次 resume 5 万条 VM 指令验证。
