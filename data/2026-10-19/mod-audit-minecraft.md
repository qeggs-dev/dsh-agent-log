<!-- 20261019-001 -->

## 项目在 〈工作区〉/mod-audit/（git 仓库、m…

项目在 `〈工作区〉/mod-audit/`（git 仓库、`main` 分支、无远端）。形态是**纯静态分析器**：无框架无构建，`index.html` 直接引 `analyzer.js` / `version.js` / `app.js`，拖入游戏目录就地分析、不上传任何文件；

另配 Electron 桌面壳（`desktop\`）出安装包。当前版本 0.16.0，产物在 `〈本机路径〉`，安装到 `%LOCALAPPDATA%\Programs\mod-audit-desktop\`。核心判断是「**模组之间的关系**好查、单个模组自身问题难查」，故只判配对关系，单模组问题降级为提示；

所有结论措辞一律「可能」+ 页头页尾声明静态分析不保证准确

<!-- 20261019-002 -->

## 三家加载器的版本语义完全不同，不能用一套通用逻辑（已由三…

三家加载器的**版本语义完全不同，不能用一套通用逻辑**（已由三个子代理分别取证）：**Forge 与 NeoForge 同源**，都用 Maven `org.apache.maven.artifact.versioning.VersionRange` + `ComparableVersion` 比较（证据：`forgespi` 的 `MavenVersionAdapter.createFromVersionSpec`、`ModInfo$ModVersion` 字段类型、依赖 `maven-artifact` 3.5.3/3.6.3/3.8.5/3.9.9）；

**Fabric 自成一套**，`VersionPredicateParser` + `SemanticVersionImpl`，语法是 `>=` `<` `~` `^` `x` `*`，空格=AND、数组=OR，且**没有限定词权重表**（纯字典序，故 `1.0-sp < 1.0` 与 Maven 相反）。

### 结论

`parseConstraint`/`cmp` 必须按加载器家族分派，不可混用

<!-- 20261019-003 -->

## Maven 侧两个必踩且反直觉的语义（都已实测）

①**裸版本号 = 无约束、匹配一切**（`versionRange="1.21.11"` 对 1.21.1 / 1.22 / 21.11.13-beta 全返回 true），不是精确匹配——真实样本 Lithium 就是这么写的；

②**空 `versionRange` = `IModInfo.UNBOUNDED`，对任何版本都返回 false**（Forge 侧缺陷，36 条真实依赖没写 versionRange 就落入此坑）。另：`[a,)`、`(,b]`、`[46, )`（逗号后空格）、`[1.0,2.0),[3.0,)`（并集）都合法；

`[a,a]` 抛 `Range cannot have identical boundaries`；限定词别名**只有四个**（`ga/final/release→正式`、`cr→rc`），`a/b/m` 不是别名

<!-- 20261019-004 -->

## 依赖比较前必须按 modId 分派已安装版本

，三家都如此：`modId="minecraft"` → MC 版本，`modId="forge"/"neoforge"` → loader 版本，`[modLoader] loaderVersion` → 语言提供者版本（Forge 是 javafml 的 `Implementation-Version`，如 `46.0`/`47.4`，**与前两者都不同**）。

区间本身不做命名空间校验，所以 `[1.21.4,)` 会"匹配" loader 版本 `21.11.13-beta`（21>1）——真实反例：`SpiderMan-1.0.3-forge-1.20.1.jar` 声明 `loaderVersion="[47,)"` 却装在 javafml=46.0 的实例里，启动即判不满足

<!-- 20261019-005 -->

## Fabric 不能假装能判定

它把 MC 版本归一化后再比对（`20w14∞→1.16-alpha.20.13.inf`、`23w13a_or_b→1.20-alpha.23.13.ab`、`26w14a→26.1.1-alpha.26.14.a`），归一化表在 `McVersionLookup.normalizeSpecialVersion` 里是 77 分支 lookupswitch，只还原了被引用到的少数几条；

且真实 mod 声明的是归一化后的值（`~26.2-`、`>=26.1.1- <26.1.1`），与实例的 `clientVersion`（`26w14a`）不在同一命名空间。因此 Fabric 模组的版本判定必须标「无法精确校验」，不许给假绿勾

<!-- 20261019-006 -->

## MC 版本/数据版本的可信来源分级（已实测）

`versions/<目录>/<目录>.json` 的 `clientVersion` 才是真 MC 版本（目录名常带加载器后缀甚至叫 `Casual`）；`id` 仅作兜底且要接纳周快照 `25w35a`；

客户端 jar 根目录的 `version.json` 里同时有 `name` + `world_version` + `java_version` + `pack_version`；

`net/minecraft/SharedConstants.class` 的常量池里是**编译期版本常量**（`VERSION_STRING`），比 JSON 更难篡改，但 NeoForge 的依赖校验**不读它**（读的是 `--fml.mcVersion` / patched jar 的 `neoforge.mods.toml`）。

**绝不从文件名猜版本**（用户明确否决：文件名谁都能改）

<!-- 20261019-007 -->

## 桌面壳打包链的现状与硬性约束

构建必须走 `npm run setup`（`node build-app.js && electron-builder --win nsis`），**直接调 electron-builder 会跳过前端复制、打进旧文件**（曾因此发出一版旧界面）；

`electron` 与 `@electron/packager` 必须在 `devDependencies`，否则 `node_modules` 被塞进 asar（201 MB → 0.14 MB）；

窗口几何已实现记忆（`userData\window-state.json`，`getNormalBounds()` + 最大化标志 + 换显示器时校验可见性）；

图标由本地生图 API 生成后经 `desktop/make-icon.py` 做圆角透明（超采样遮罩 + LANCZOS），`rcedit` 需要文件符号链接权限（开发者模式或管理员）

<!-- 20261019-008 -->

## UI 动效的同名坑一天踩了四次（侧边栏、注入点列表、高危…

UI 动效的**同名坑一天踩了四次**（侧边栏、注入点列表、高危高亮、版本统计面板）：CSS `animation` 的 `fill-mode: both` 会**持续占用被动画的属性**，此时用 `transition` 去改同一属性、或靠 `animation: none !important` 取消动画，浏览器都**不会**把它当作可过渡的变化，属性直接跳到终点。

### 定论

入场动画只在**一次性类**上挂（`.fresh`，且播完必须摘掉），退场一律用 `transition`；`display:none` 的元素无法过渡，要用 `visibility + opacity`（`visibility 0s linear <duration>` 延迟隐藏）。

### 另一个同类坑

`cursor` 要写在**实际被命中的元素**上（`#dropzone` 是 `inset:0` 的全屏遮罩，写在 `canvas` 上永远不生效）
