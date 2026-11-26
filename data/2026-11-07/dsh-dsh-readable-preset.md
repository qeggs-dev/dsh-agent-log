<!-- 20261107-003 -->

## DSH 浮层的「毛玻璃」是三件套，只写背景色会变成透明

（0.2.2-rc.1 实测，可读预设菜单首版即踩）：①`background: var(--dsw-specific-menu)`＝`var(--dsw-menu-surface-fill)`，本身是**半透明**色（浅色 `#fcfdfeb3`、深色 `#303136a3`，darwin 平台另有 `#f8f9faf0` / `#303136f0` 覆盖）；②`backdrop-filter: var(--dsw-menu-backdrop-filter)`＝`blur(40px) saturate(150%)`，**模糊全靠这一条**，缺了它半透明底色就直接透出背后内容，观感是「透明」而不是毛玻璃；③`box-shadow: var(--dsw-elevation-panel)`（内含 0.5px elevation stroke，所以不需要再手写 border）。深色主题的描边色由 `body[data-ds-dark-theme] [data-menu-material]` 提供，因此浮层元素要带 `data-menu-material` 属性。token 定义在 `@deepseek-ai/dsh-client-ui-theme/lib/client.js` 的内联 CSS 里（`Theme.listTokens` 只列 14 个公开别名，查不到这些 specific/menu token，别据它判断 token 不存在）。
