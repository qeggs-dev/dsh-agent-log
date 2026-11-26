<!-- 20261101-006 -->

## 插件「shell .env 加载」

（`〈工作区〉/dsh-pwsh-dotenv`，包 `@local/dsh-pwsh-dotenv` v1.0.0，desktop profile bundle，行 id `pwsh-dotenv` / entry `include:pwsh-dotenv`，`application: applied`、`fiberPhase: active`）：**注册一个独立工具 `pwsh_dotenv`**——跑 PowerShell 时把该次命令工作目录下的 `.env` 载入环境。

**原 `pwsh` 工具完全未改**（不拦注册、不改原型、不碰别人的定义）。参数只有 `command` / `description` / `workdir` / `timeoutMs`；

结果文本与 `pwsh` 同一套标记（`[stderr]`、`[sandbox: …]`、`[timed out after Nms]`、`[killed by signal: X]`、`[exit code: N]`），终端卡片同样把退出码收成 pill，只在最前面多一行 `[env: N variables from <path>]` 或 `[env: no .env in <dir>]`（注记必须在头部——退出码 pill 从尾部解析）。

### 优先级

受管 `DSH_*`（经 `ctx.shellEnv.collect` + 执行器最后合并）最高 → 宿主进程已存在的同名变量不覆盖（dotenv 默认，避免 `.env` 的 `PATH`/`TEMP` 破坏命令）→ `.env` 其余值。

`lib/dotenv.js` 是零依赖 dotenv 兼容解析器（注释、`export ` 前缀、单/双/反引号、双引号 `\n` 转义、CRLF、BOM；**不做 `${VAR}` 展开**）；文件 >512 KiB 视为不可用，解析按 `size+mtime` 缓存。

### 刻意缺两项

`run_in_background`（`ctx.jobs` 接线属官方工具）与 `sandbox_permissions`+`justification`（升级审批流在 `@deepseek-ai/dsh-sandbox`），工具描述里已写明让模型改用 `pwsh`。

测试 22 项全绿（`tests/dotenv.test.mjs` 11 + `tests/tool.test.mjs` 11：合并/覆盖规则/相对 workdir/策略透传/渲染/卡片）。

<!-- 20261101-007 -->

## 为什么最终改成「另开工具」而不是「给 pwsh 加参数」

DSH **没有**给已有工具加参数的扩展点（`register` 重名抛 `tool "x" is already registered`；`tools.guard()` 只否决；`tools/pre-execute` 不改写参数；

patch 里 `name` 只能断言不能改名），唯一缝隙是**拦 `ToolRuntime.prototype.register`**。该方案曾**跑通并实测生效**，但代价过高：①还要包 `ShellExecutor.prototype.execute` 才能把环境塞进已 resolve 的 spec；

②依赖 `defineTool` 的构造期闭包——它在注册时就把参数表转成 JSON Schema 并用闭包做校验，而 `schemaOf` 每次读 `definition.parameters`，所以换参数表后**必须把新键从实参剥掉**再交给原 execute/`presentCall`/`presentResult`（`additionalProperties:false` 时校验器会对未声明键报错）；

③被 HMR 挂载顺序反噬（见 20261101-008）。

独立工具只依赖**公开 seam**：`ctx.shell.resolve(request)` 接收 `request.env`（`dsh-pwsh-local` 按 `{...ENV_OVERRIDES, ...spec.env, ...spec.dshEnv}` 合并）、沙箱/截断/spill/超时/取消全由执行器负责。

代价是模型多一个近似工具，用描述里的「何时用它、何时用 pwsh」来界定。

<!-- 20261101-008 -->

## HMR 挂载顺序的通用教训（踩过一次真坑）

`install_bundle` 走 HMR 时是**新 fiber 先挂、旧 fiber 后卸**。

任何「检查已打过补丁就跳过」的插件在这种顺序下会让新 fiber 什么都不装，紧接着旧 fiber 卸载把原型还原成原始版本 —— 症状是 `list_plugins` 显示 `enabled:true / fiberPhase:active`，但能力**根本没生效且无任何报错**（当时新会话里 `pwsh` 连 `load_env` 参数都不存在）。

若以后确实要打补丁，必须**引用计数**（记录挂 `globalThis`，跨 fiber/跨模块代数可见，`refs+=1` 复用同一 wrapper，最后一个持有者释放才还原），不能只用布尔标志。另：**改本插件源码必须重启 App**（模块被缓存；

HMR 只重跑行、不重新 import 模块），只改 patch 里的行/配置可热生效。
