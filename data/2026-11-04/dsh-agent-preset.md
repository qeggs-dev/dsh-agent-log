<!-- 20261104-006 -->

## 工作区根 `super_workspace.json` 已按记忆…

工作区根 `super_workspace.json` 已按记忆写入两个外部工作区（用户要求）：`normal` → `D:\Projects\DSH_Normal_Workspace`（第二工作区，正常目录；

按任务建子目录、根目录保持干净、子目录可留）、`work` → `G:\work`（第三工作区，共享式按位置命名；项目子目录现有 `adl` / `cordis-host` / `dlcore`，构建产物 `<项目>\out\`、可执行副本与独立 userData `<项目>\run\`）。

`super_workspace_list` 显示两者 available；`super_workspace_exec` 实测 `normal`、`work` 根目录，以及 `work` + `workdir: "dlcore"` 落在 `G:\work\dlcore`（内容 `out` / `run`）。

 （2.0 起该文件只用于一次性导入，之后忽略）
