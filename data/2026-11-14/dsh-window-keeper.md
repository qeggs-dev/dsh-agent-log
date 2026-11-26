<!-- 20261114-018 -->

## dsh-window-keeper 在 2026-11-14 D…

dsh-window-keeper 在 2026-11-14 DSH 升到 0.2.2-rc.3 后「又不能工作」，根因不是版本不兼容（新版本里插件照常加载），而是 2026-11-13 迁入 dsh_plugins\ 时留下的两个坑：①状态文件路径写死在插件目录内（旧 patch 的 stateFile 指向 dsh-window-keeper\window-state.json），迁移只搬目录、patch 仍指旧路径，旧路径成了空目录 → 插件判定「没有历史」，把当时的壳默认尺寸 1296x828（1280x820+边框）存成第一次状态，于是每次启动都还原成默认尺寸；②迁移时在同进程里二次 install_bundle，createWin32() 重复 koffi.struct('DSH_WINDOW_KEEPER_RECT') 抛 Duplicate type name，插件直接把自己 disable 掉，当晚再没记录过。修复：declare() 先 koffi.type(name) 复用已有类型、取不到才 koffi.struct 新建；patch 改成 config: {}，状态文件走默认的 %APPDATA%\@deepseek-ai\dsh-desktop\desktop\window-state.json，并把当前几何 1895x1073@346,239 作为种子写进去。重启后（pid 48504）日志 applied 1895x1073 at 346,239、窗口实测同值；插件仓库已提交 e0f73d7（含 .gitignore、删掉被跟踪的旧状态文件，旧文件移到 .tmp\window-keeper-legacy\）。教训：插件持久状态不能放插件目录；同一进程里的 HMR 重复加载必须幂等。
