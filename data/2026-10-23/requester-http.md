<!-- 20261023-020 -->

## 修掉 Requester「运行一次后新建块选不中 / 侧边栏卡在上一个块」

（用户报的现象：运行过一次之后新建的块点不动，只有已存在的块能选，重启才恢复；单测 156 → **159 项全过**，安装包 00:44:46 / smoke exit 0）。根因：`ui.ts` 里的 `newBlock("request")` 还写着字段改造前的默认值 `headers: {}`（对象），而现在 `RequestSpec.headers` 是**行数组**；渲染新块时 `rowsOf(...).map` 对对象调用 → TypeError 从 `renderEditor()` 抛出 → `render()` 中途中断 → `#tab-edit` 保留上一次 innerHTML（所以看起来"还是上一个块"），点击新块每次都同样抛错，UI 就再也切不过去；重启后从磁盘读会走 `parseHeaderRows` 把对象转成数组，于是又正常了——这解释了"只有重启能恢复"。修法三层：①新建块的默认值搬到纯模块 `src/shared/new-block.ts`（`headers: []`/`params: []`/`body: {mode:"none"}`，去掉遗留的 `target` 字段），并有单测钉住"形状必须合法、能被 parseWorkspace 接受、不含 undefined"；②`rowsOf`/`formRowsOf`/`renderRowTable` 对非数组做就地修正与兜底，坏数据不再能炸渲染；③`renderEditor` 包 try/catch，单块渲染失败只在该面板显示"这个块渲染失败 + 原因"，不再让整个界面停在上一个块。真机验收：运行整组一次后新建 请求/等待/变量/顺序组/并行组 都能立刻选中（侧边栏名字/请求编辑器正确），7 个已有行逐个点全部配对，无"渲染失败"。
