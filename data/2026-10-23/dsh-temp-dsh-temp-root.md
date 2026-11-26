<!-- 20261023-034 -->

## dsh-temp-root 已从旧写法改成新版 bundle 写法

（旧写法＝单个 `src/temp-root.mjs` + profile patch 里手写 `file://` 行）。

工作区 `dsh-temp-root\` 现在是一个完整包：`package.json` 里 `dsh.bundle.patch: ./cordis.patch.yml`、`exports` 为 `.` / `./locale/*.json` / `./icon`、`files` 只列 `index.js`+patch+locale+icon+README；

实现搬到根目录 `index.js`（纯 ESM、只用 `node:` 内置模块，只 export `name` 与 `apply`，**不再有 default export**——`name`+`apply` 与 service class 是二选一的形式，不能混）；

`cordis.patch.yml` 即 bundle patch（插 id `temp-root`、name `@local/dsh-temp-root`，config 为 root/create/verify/ensureFullControl）；

新增 `locale/{en,zh}.json`（`meta.title`/`meta.description`）与 `icon.svg`。

旧 `--patch` overlay 保留为 `run-from-source.patch.yml`（file:// 指向 **index.js** + spill-local 覆盖），`start-dsh-web.ps1` 已改用该文件；

`src/` 已删除，`tests/*.mjs` 改为 `import '../index.js'`。

<!-- 20261023-035 -->

## 桌面 profile 的 temp-root 现状

（当日实测）：`@local/dsh-temp-root` 经 `plugin_manager install_bundle`（target = 工作区目录）装进 desktop profile —— profile `package.json` 多一条 `"@local/dsh-temp-root": "link:D:/Projects/Deepseek_Harness_Workspace/dsh-temp-root"`，`dsh.profile.bundles` 末尾追加 `@local/dsh-temp-root`；

插件行 id `temp-root` 现在由 bundle 自带 patch 提供（`Config.listConfigs` 用 name `@local/dsh-temp-root` 可查到 `patchId: temp-root`，`status: absent` 表示插件没声明 Config schema）；

profile 自己的 `cordis.patch.yml` 的 temp 段只剩注释与 `- id: spill-local` 的 root 覆盖，旧手写 `file://` 行已删。

重启后实测 `TMPDIR=D:\Deepseek_Harness_Temp`、`TEMP`/`TMP`= 它下面的 `dsh-<rand>` scratch，pwsh 与写文件均正常。**bundle patch 不在 HMR 监听范围**（只有 profile 自己的 patch 是），改它要重启。

<!-- 20261023-036 -->

## 换 temp-root 行/实现的坑（本次差点踩中）

两个 temp-root 实例同时活着时，**先卸载的那个会把 env 还原成自己 apply 前的值** —— `restore()` 只判断「当前值是否仍等于自己写的 root」，两个实例写的 root 相同就区分不开，于是进程退回 `R:\Temp`（沙箱与所有受限调用全挂）。

### 本次实际顺序

①profile patch 里把旧行 id 改名 `temp-root` → `temp-root-legacy`（避免与 bundle 行同 id）②`install_bundle` ③删掉旧行（此时 env 确实被还原成 `R:\Temp`）④立刻重启，由 bundle 行在 boot 时重新采纳。

### 更稳的顺序

改名 → 装包 → 重启 → 再删旧行（重启后旧行的 previous 已是新行写的值，删它不再回退，全程不掉）。

另两条 loader 语义（0.2.1-rc.2 的 `dsh-app-boot/lib/index.js` 里 `applyEntryPatches`）：`insert` 是**追加且不查重**（同 id 两行会各挂一次）；

**非 insert 的覆盖必须 `name` 与既有行一致**，写不同名字会被 "name mismatch … skipping" 跳过——即**不能用覆盖改 name，改名只能删行+插行**；profile patch 层在全部 bundle 层之后应用。
