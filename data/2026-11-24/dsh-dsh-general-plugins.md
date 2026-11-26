<!-- 20261124-002 -->

## 2026-11-24 新增并安装 DSH 插件 `@local/…

2026-11-24 新增并安装 DSH 插件 `@local/dsh-general-plugins`（目录 dsh_plugins/dsh-general-plugins，独立 git 仓库）。它在设置侧栏新增「常规插件设置」（settings.section id `general-plugins`，order 14，位于「模型」与「内置插件」之间），页面用横向标签页收集只有少量选项的插件设置。跨插件扩展点不是槽位而是客户端 Cordis 服务 `generalPlugins`：调用方用 ctx.inject(['generalPlugins'], scope => scope.effect(() => scope.get('generalPlugins').register({ id, label, order, component }), ...)) 注册一个标签页（label 可传 thunk 随 locale 重读，返回幂等 disposer），查询用 .list()。内置「显示」页（记住上次打开的标签页，偏好存 localStorage 的 dsh.general-plugins.remember-tab / -last-tab）与「概览」页也走同一 register 接口；某标签页抛错由页内 error boundary 隔离。已现场验证：第三方临时插件注册的标签页能出现、按 order 排序、可切换、移除后消失；亮/暗主题均只使用 --dsw-alias-* / --dsw-focus-ring-* token。本插件只有客户端半，Host index.js 的 apply 为空，没有工具、路由或配置。
