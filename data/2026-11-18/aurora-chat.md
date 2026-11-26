<!-- 20261118-007 -->

## DSLike Chat 更名为 Aurora Chat（2026-11-18）

应用显示名/窗口/页面标题/关于页/首启弹窗全部改为 Aurora Chat；包标识 com.dslike.chat → com.aurorachat.app（桌面 appId、Android applicationId/namespace、Java 包路径迁移）；

产物改为 out/aurora-chat-desktop-<v>-win-x64.zip 与 out/mobile/aurora-chat-debug.apk；

App 图标换成极光图形（assets/brand + tools/brand/gen-aurora-icons.mjs，确定性生成，无 DS/官方元素），Android mipmap/splash 同步；

内部标识（localStorage chat-demo:*、IndexedDB dslike-*、CSS --dslike-*、dslike_chat.style_pkg 资源前缀）保留并写进 README。

0.3.3 发布（web eefb802 / root c348c20）：极光包内置为默认样式包（build-web 复制 tools/style-fixture/aurora.zip 到 web/src/assets/builtin，启动 ensureBuiltinPack 写入 IndexedDB 并默认启用，不可删除、版本升级自动更新、删用户包回退内置包，移除“停用样式包/回上游外观”入口）；

关于页与首启弹窗加官方在线体验链接 https://cdn.deepseek.com/chat-demo（上游官方 demo，标注无关）；根 LICENSE/package author 改为 Aurora Chat contributors，示例包作者同步、版本 1.2.2。

### 注意

改名换包名后 Android 旧 App（com.dslike.chat）与桌面旧 userData 数据不会自动迁移。

<!-- 20261118-011 -->

## 待办（0.4）

把 App 打包使用的图标换成亮色版（用户已确认范围：不是 UI 图标，也不是启动屏文字，而是打包进桌面/Android 的应用图标）。

### 做法

以 aurora-light-512/1024 素材生成 desktop/build/icon.png、Windows NSIS 安装器图标、Android mipmap（普通/圆形/自适应）与必要启动屏；保持无字母/无官方元素；

在浅色任务栏/桌面背景与 16/32px 下验证可辨识，与现有深色版可二选一或保留深色作 fallback。

<!-- 20261118-013 -->

## Aurora Chat 路线图（2026-11-18 用户确认）

0.4 的主题是**大量动效**，不是近期工作；

亮色 App 打包图标的待办不挂在 0.4 上，改为「下一个 0.3.x 顺手做」的独立项（范围仍是打包图标：desktop/build/icon.png、NSIS 安装器图标、Android mipmap/启动屏，用 aurora-light 素材，验证 16/32px 与浅色任务栏可辨识）。

### 近期可排期项

插件运行时（Cordis Phase 2 + Worker/iframe 沙箱 + 首次外部插件安装三次确认）、导入预设只读 UI 实测、0.3.x 小修。
