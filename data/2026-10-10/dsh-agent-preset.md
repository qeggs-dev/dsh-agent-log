<!-- 20261010-002 -->

## 加预设的配套改动与验证

`dsh-desktop-presets\generate.mjs` 的 `MODES[]` 追加 `{ id:'confident', order:16, meta:{...} }`（description 是 GUI 卡片文案；不写 `keep` 即自动全保留 standard 的 19 行）；

`dsh-desktop-presets\tests\append-logic.test.mjs` 的 `expected` 预设行清单补上 `preset-confident`——**该断言写死了预设清单，以后每加一个预设都必须同步改它**。

### 实测

`node generate.mjs` 写出 70258 字节；`--append` 报「生成段 874 行 → 1071 行；其后 6 行原样保留」；回归测试四条断言全 PASS（尾部含 `selectedDefault: collab` 逐字保留）；

profile patch 现有 8 个用户预设（chat 9 / collab 10 / plan 11 / introvert 12 / pity 13 / slacker 14 / discuss 15 / confident 16），`selectedDefault` 仍为 collab、未改动

<!-- 20261010-006 -->

## 新增桌面版预设吃瓜模式（config.id gossi…

新增桌面版预设**吃瓜模式**（config.id `gossip`，patch 行 id `preset-gossip`，order 17；

live 树里 `include:preset-gossip` 已 status=schema，新增行 HMR 热生效、无需重启）：定位是「当前工作区 = 信息源」——**工具集与协作模式逐行完全相同**（19 个顶层行，id 与顺序与 collab 一一对应，由新增的结构测试代码级验证），差别全在 persona：把工作区当作**要拿来聊的材料**而非待办项目，先读再谈、读完要有自己的判断（带依据的看法、指出值得再看的地方），发现错值 / 矛盾只当话题不顺手改；

未获授权不做任何留痕动作。persona 源文件为工作区 `dsh-desktop-presets\personas\gossip.txt`（4569 字符，自 discuss 的 4309 字符同源改写，结构段与 discuss 基本一致，新增 "Have a take." 一段）。

### 配套改动

`generate.mjs` 的 `MODES[]` 追加 `{ id:'gossip', order:17, meta:{name:'吃瓜模式', description:...} }`（放在 confident 之后以与 order 同序）；

`tests\append-logic.test.mjs` 的 `expected` 清单补 `preset-gossip`；

**新建** `dsh-desktop-presets\tests\structure.test.mjs`（只读结构测试：除刻意裁剪的 plan/slacker 外每个预设的顶层行须与 standard 逐行一致，且 gossip 必须与 collab 逐行相同，并断言生成段含 `id: gossip` / `order: 17` / `name: 吃瓜模式`）。

### 实测

`generate.mjs` 写出 82307 字节；`--append` 报「生成段 1071 行 → 1234 行；

其后 6 行原样保留」，profile patch 现 119790 字节、9 个用户预设（chat 9 … confident 16 / gossip 17），`default: standard` 与 `selectedDefault: collab` 均未改动；两个测试全部 PASS

<!-- 20261010-007 -->

## 用户当日对吃瓜模式追加要求（原话近义

「不那么急迫的直接上手，而是逐个点破」）——即节奏改为**一次只点破一处**：发现值得说的东西就只说这一件、停下等用户回应，不把一堆发现塞进同一条回复，也不因为「反正该做」就抢跑；**获授权的执行同样一次只走一步**（一步 / 一个文件 / 刚谈成的那一点），批量编辑与铺开式重写不属于这个模式。

落地为 persona 三处改动（源文件 `dsh-desktop-presets\personas\gossip.txt`，4309→4569→**5779** 字符）：①"What counts as action" 段后新增 "Point it out one at a time." 整段（unhurried by design / 没有东西必须在本轮处理 / 一次一件 / 别把单个发现变成小雪崩 / 能让用户接得上话的回答胜过完整回答）；

②授权段的 "do it properly and keep going until it is finished, then return to discussion" 改为 "do it properly — but do not treat the permission as a licence to race ahead"（授权≠抢跑，一步一停、批量编辑不是本模式）；

③结尾句补 "or rushing through authorized work faster than they can follow it"。`generate.mjs` 里 gossip 的 `meta.description` 同步补「一次只点破一处」「获授权后同样一次只走一步、不抢跑」。

### 实测

`--append` 报「生成段 1234 → 1236 行；其后 6 行原样保留」，工具集仍是 19 行且与 collab 逐行一致（结构测试 PASS），两个测试全 PASS，HMR 热生效无需重启
