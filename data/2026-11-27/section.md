<!-- 20261127-004 -->

## 决策（2026-11-27，rawcall 的三条架构选择）

①**不用 libffi，C 核心用 switch 穷举参数个数**：x64 Windows 只有一种调用约定（前 4 个整数参数进 RCX/RDX/R8/R9，其余压栈），而本项目只传整数与指针（用户的设计风格是「像 C 一样直接定义内存数据并传给系统 API」），指针与整数在 ABI 层没有区别，所以 `((uint64_t(*)(uint64_t,...))p)(a0,...)` 一个 switch 就够。

libffi 只在浮点参数、结构体 by value、可变参数时才必要，Win32 基础 API 里这三样都少见。这是全项目最大的复杂度削减：不构建 libffi、不用 vcpkg、不受 MSVC/MinGW 混用影响。

②**三语言 SDK 共用 CONTRACT.md 的 13 个概念命名**：loadLibrary/unloadLibrary/resolve/alloc/free/zero/readU8..U64/writeU8..U64/readBytes/writeBytes/writeUtf16/call/lastError；

命名一致但大小写按语言规范（Python snake_case、Java/JS camelCase），允许资源管理形态差异（Python with、Java AutoCloseable、JS dispose），禁止发明同义词、禁止合并概念（alloc 与 zero 分开）。

③**C 核心只做四件事**（加载/卸载、解析符号、内存与标量读写、按 ABI 调用），任何协议知识/类型系统/签名数据库都不进这一层；因此签名从「地基」降级为「可选增强」，因为定位就是使用者自己知道参数是什么。

验收链路固定为 GlobalMemoryStatusEx（load→resolve→alloc(64)→write_u32(0,64)→call→read_u64(8)>0），它同时验证句柄、符号、分配、写、调用、读回、释放，且 dwLength 填错会直接失败（结构体布局错误会暴露）。
