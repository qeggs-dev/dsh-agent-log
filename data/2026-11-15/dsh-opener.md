<!-- 20261115-014 -->

## dsh-opener 打包成「给 Agent 的 skill bundle」（0.1.0，2026-11-15）

用户原话「帮我打包一下 dsh-opener 插件 / zip 格式，我给我朋友的 Agent 发过去 / 要带一个 SKILL.md 用于安装」，随后补充「对面也是 DSH」——所以 SKILL.md 走 DSH 自己的安装路径（plugin_manager install_bundle + restart_dsh），不需要为别的宿主写兼容说明。

按 R-020 出两件产物，都在 `dsh_plugins/dsh-opener/dist\`（已 gitignore）：`dsh-opener-0.1.0.tgz` 16,513 B sha256 `73e70228a9990cb36f2d04cc716ee555864b8807b45ef9e4b292c1e775b2be3b`；

`dsh-opener-skill-0.1.0.zip` 26,997 B sha256 `9835e55f37b8a838db3b19008cec9d0a7b657ad3c3eea855014d7ec0efab99ef`。

zip 根是 `dsh-opener\`，4 条目：`SKILL.md`（frontmatter name/description/whenToUse，正文含 contents/dependencies/install/verify/configure/remove/help）、`references\customization.md`（config 全字段与校验规则、`window.dshOpener.open` 运行时 API、replay 事件、全部时间常量 2750/2150/450/900/2200/12000/900）、`references\troubleshooting.md`（症状→原因→修法矩阵、`dsh --profile … --dump-config`、干净重装、报障要收的信息）、`plugin\dsh-opener-0.1.0.tgz`。

**打包源在仓库 `packaging\`**：`packaging\skill\` 手写 SKILL.md 与 references，`packaging\build.ps1` 先 `pnpm pack`（吃 `files` 白名单，9 个文件：index.js/client.js/cordis.patch.yml/locale 两个/docs/DETAIL.md/README.md/icon.svg）再 stage 成 zip；

build.ps1 还会核对 SKILL.md 里引用的 tgz 文件名与 package.json 版本一致，防止版本漂移。

README 加「Install」「Packaging and distribution」两节，提交 `3064906`（5 files, 408 insertions）+ `9379272`（措辞修正）+ `239d421`（补无 plugin_manager 时的降级安装路径）。

**版本保持 0.1.0**（从未分发过，无需像 dsh-ui-port-mirror 那样为打包抬版本）；**仍不加 `engines.dsh`**（管理器会按它拦安装，范围语义没实测）。

### 实测

tgz 只含 9 个运行文件、无 verify 脚本；`node --check index.js client.js` 通过；`import('./index.js')` 得到 `[apply]`；

临时 pnpm 工程 `pnpm add <tgz>` 1.3–1.9 s 装好、入口与 `client.js` 解析正常（临时目录已删，无 .pnpm-store 残留）；zip 解压后 4 条路径与源文件 sha256 逐一相等；

**SKILL.md frontmatter 用 DSH 自己的解析器验过**（`@deepseek-ai/dsh-skill-filesystem` 用 `yaml` 包 parse，实测读回 name=dsh-opener、description 414 字符、whenToUse 169 字符、无多余键）。

### 本轮从代码里确认的两条事实

此前只有转述：①skill 根由 `dsh-skill-filesystem` 的 `roots()` 给出——`<projectRoot>/.dsh/skills`、`<projectRoot>/.agents/skills`、`<DSH_HOME>/skills`、`<agentsHome>/skills`，目录包形态是「`<root>/<name>/SKILL.md`、深度一层」；

②`install_bundle` 只往 profile `package.json` 写依赖，行本身来自包自带的 `cordis.patch.yml`，用户要改内容是在 profile `cordis.patch.yml` 加**同 id 的覆盖行**（该文件注释写明「applied after every bundle layer: id-targeted config overrides」），所以 SKILL.md 里不要写「profile patch 里有 dsh-opener 行」当安装校验。

### 未验证

没把包用 `install_bundle` 装进另一个 profile（会改本机桌面 profile），也没把 zip 放进 skill 根用 provider 真发现一次（不想动用户 skill 目录）；

对面 DSH 的版本未知，SKILL.md 因此声明「验证于 0.2.2-rc.3」并列出 hook/slot 缺失时的失效方式。
