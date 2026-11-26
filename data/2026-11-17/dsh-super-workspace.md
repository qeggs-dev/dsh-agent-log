<!-- 20261117-010 -->

## dsh-super-workspace 的工作区菜单项「外部工作…

dsh-super-workspace 的工作区菜单项「外部工作区…」在 DSH 0.2.2-rc.3 上消失，根因是竞态而非 API 变更：客户端插件在 apply 里用 ctx.get('contextMenus') 取菜单注册表，而该服务由 @deepseek-ai/dsh-client-ui-context-menu 的 apply 提供，后者自身 inject 了 slots/locale/shortcuts，apply 会被推迟；

我们的 apply 只 inject slots/locale，先跑完且 ctx.get 返回 undefined，于是静默跳过注册（shell.overlay 里的对话框仍注册，所以看起来“插件是好的”）。

### 修法

改用 ctx.inject(['contextMenus'], scope => { const menus = scope.get('contextMenus'); scope.effect(() => menus.register({id,target:'workspace',order,resolve})) })，服务出现时再注册。

### 通用教训

客户端插件里凡是由他人插件提供的服务，不要在 apply 时一次性 ctx.get 后静默跳过，用 ctx.inject 等待；否则改版或加载顺序变化就会让入口无声消失。

版本 2.1.1，改后页面 reload 即生效（bundle 每次 reload 从磁盘取，rev 字符串不随内容变，不要用 rev 判断是否已更新）。
