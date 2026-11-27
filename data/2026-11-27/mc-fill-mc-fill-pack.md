<!-- 20261127-007 -->

## 工作区 mc-fill-pack/（2026-11-27 建）

Minecraft `/fill` 指令体积检查与超限分包的单文件网页工具，用户需求原话「填入一个 MC 的 fill 命令 → 检查体积是否过大 → 合法就判定合法 → 过大就输出一个指令包文件」。成品 `dist/fill-checker.html`（约 65 KB，无外部依赖，双击可用，file:// 可跑）；

逻辑在 `src/` 按模块拆（util/coords/parser/geometry/splitter/commands/planner/crc32/zip/datapack/ui/main），`build.mjs` 把 ES 模块内联成单文件并做 `vm.Script` 语法检查与注入完整性检查（曾因 `String.replace` 把 `$'` 当替换模式、把模板尾巴插进脚本，故注入必须用函数式替换）。

判定默认上限 32768（Java/基岩一致，界面可改）；纯绝对/纯相对体积与执行位置无关，混合坐标按「基准坐标」展开，`^` 明确拒绝；

超限时选「切完块数最少」的轴贪心切分，每块 ≤ 上限且不重不漏（node:test 65 项，含逐方块覆盖校验），产出带 pack.mcmeta 的 .zip（1.21 用单数 `function/`，旧版 `functions/`，pack_format 表内置）；

可选每 tick N 条 schedule 分批，此时把 `~` 展开成绝对坐标（schedule 会改变执行位置）。

### 已知限制

hollow/outline 拆开会改变外观（有警告）、不校验方块 ID、基岩版语义有差异。

### 测试

`node --test --test-isolation=none "tests/*.test.mjs"`。
