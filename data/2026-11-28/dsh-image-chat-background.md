<!-- 20261128-003 -->

## image-chat-background（@local/image-chat-background 0.1.0）新建并安装

用户要求「在设置页面里自定义一个视频或图片，样式含点阵图、曝光(正负)、亮度(正负)、九宫格对齐，视频内容也可以放图片，可存成预设下一次快速切换」。目录 `〈工作区〉/dsh_plugins/image-chat-background`（独立 git 仓库、4 个提交、无构建步骤）。

### 结构

宿主 `index.js` + `lib/config.js`（纯设置模型/归一化/预设匹配）、`lib/media.js`（文件头嗅探、扩展名→MIME、Range 解析）、`lib/http.js`（JSON/上传流/带 Range 的文件响应/写入口）、`lib/store.js`（state.json 原子写 + media 目录）；

浏览器半 `client.js` 单文件（`window.__ModuleLoader__` 工厂，无 import），含壁纸层、设置页与预设 UI。

### 入口

`settings.section` id `image-chat-background`、order 21，另注册 `settings.section.icon`；文案走 `ctx.locale.register('imageChatBackground', {zh,en})`。

### 壁纸怎么贴上去

宿主没有给聊天区背景留 slot，层挂在 `[data-conversation-content]` 的第一个子节点，并给该节点 `isolation:isolate`，层 `position:absolute;inset:0;z-index:-1;pointer-events:none` 才能既盖住底色又落在消息之下；

会话切换重建节点时用 MutationObserver 重新挂载，卸载时移除层并还原 isolation。

### 样式映射

曝光 = `filter:brightness(2^(v/100))`；亮度 = 白/黑蒙版（最多 90% 不透明）；九宫格 = `object-position` 的 9 个锚点；

点阵图 = 把**媒体本身**用 `radial-gradient` 遮罩切成圆点（mask-size 3–40px 点距，遮罩半径 5–95% 点径），默认 8px/45%；contain 时用 `--dsw-alias-bg-base` 补边。设置页预览与聊天区共用同一段 DOM 渲染函数，所见即所得。

### 路由

前缀 `/dsh-image-chat-background`：GET `state`、`file/<name>`（支持 Range，视频可拖动）；

POST `config`、`enabled`、`presets/save|apply|delete|rename`、`media`（请求体即文件）、`media/remove`、`media/prune`。读取过宿主 `connection.requestRejection`（浏览器准入）；写路由另判 Origin。

上传按文件头判定真实类型，接受 PNG/JPEG/GIF/WebP/AVIF/MP4/WebM，拒绝 SVG 与伪装 MIME。

### 存储

`$DSH_HOME/plugin-data/image-chat-background/state.json` + `media/<id>.<ext>`（id 命名、永不原地改写，可长缓存）。替换素材或删除预设都不删文件，只有显式 `media/prune` 才删「当前设置与所有预设都不再引用」的文件。

单文件上限默认 256MB（Config.maxMediaBytes，1MB–2GB）。

### 验证

39 个单测（`node --test-isolation=none --test "tests/*.test.mjs"`）全绿，含设置页组件的一次真实渲染；

真机上传 1.3MB PNG 与现场用 MediaRecorder 录的 WebM，视频静音自动播放（readyState 4）、点阵/对齐/曝光/亮度/填充方式/预设保存与切换都用设置页点击验证；浅色与深色主题各截图看过；插件卡显示中文标题、描述与自绘图标；测试素材与预设已清理、壁纸最终关闭。

安装 `install_bundle` 返回 `application: applied`，宿主改动靠 restart_dsh 生效。

### 已知限制

壁纸全局一份、不分会话/工作区；跨窗口只在重新获得焦点时同步，不轮询；不注册任何模型工具。
