<!-- 20260918-001 -->

## VES（Virtual Environment System）源…

VES（Virtual Environment System）源码位于 `〈项目目录〉/Python/VES`，入口脚本 `ves.py`，是一个用 Python 3.14 编写的虚拟环境管理交互式 CLI；其虚拟环境基目录默认为 `〈工作区〉/envs`

<!-- 20260918-002 -->

## 启动 VES 用工作区根目录的 ves.bat，该批处理等价…

启动 VES 用工作区根目录的 `ves.bat`，该批处理等价于执行 `python 〈项目目录〉/Python/VES/ves.py`；工作区里只有这个启动器，没有 VES 源码

<!-- 20260918-003 -->

## VES 启动后进入 > 交互提示符，help 打印全部命令

create、chbase、ifr、shell、repl、install、uninstall、copy、cmdls、freeze、list、remove、delete、print、title、set_var、set_const、get_var、remove_var、set_var_from_ret、set_const_from_ret、jump、je、jne、jlt、jgt、jle、jge、jt、jf、execute、recursive、help、exit；

完整 help 输出实录见附件

<!-- 20260918-004 -->

## VES 需要真实 TTY

在无控制台的管道环境（Agent 的 shell）中 stdin 立即 EOF，程序打印 `EOF Error` 后退出，无法人工交互；非交互验证需把命令经 stdin 管入，例如 `"help" | .\ves.bat`

<!-- 20260918-005 -->

## VES 当前状态

可正常启动并执行 `help`，横幅、Base dir、Python 版本与命令清单均输出正常

<!-- 20260918-033 -->

## VES 支持命令行模式

`ves.bat <command> [args...]` 直接执行单条命令（`ves.py` 取 `sys.argv[1:]`、把首个 token 小写后按命令表分派），这是无 TTY 环境下真正可用的入口；

`ves.bat create net`、`ves.bat install net <包名>`、`ves.bat list` 均按此执行，无须进入 REPL

<!-- 20260918-034 -->

## install/uninstall 一次只接受一个*…

`install`/`uninstall` 一次只接受**一个**包（签名 `(env_name, package)`），装多个包必须分多次调用；要一次装多包需用 `ifr <env> [requirements_file]`，该文件默认 `./requirements.txt`（相对 cwd）

<!-- 20260918-035 -->

## VES 的进程退出码不可信

失败往往只打印 `Error: ...` 而进程仍以 0 退出（实测 `ves.bat install no-such-env pydantic` 报 WinError 2 却 exit=0；因为 `_install_cli` 无 return、`main()` 又丢弃 `match_cmd` 的返回值）。

判断成败要看输出里的 `Exit code: N` 统计行（由 `print_run_statistics=True` 打印，仅在该命令**确实**启动了子进程时才有）或直接调 pip 复查；只有 `remove` 这类抛未捕获异常的路径才会非零退出

<!-- 20260918-036 -->

## freeze <env> 在命令行模式下不打印任何结果*…

`freeze <env>` 在命令行模式下**不打印任何结果**（返回值被忽略，只有传 `output_file` 参数才落盘），要拿依赖清单直接调 `envs\<env>\.venv\Scripts\pip.exe freeze`

<!-- 20260918-037 -->

## VES 的环境基目录取 Path.cwd() / "envs"…

VES 的环境基目录取 `Path.cwd() / "envs"`，所以必须在工作区根目录运行 `ves.bat`，否则环境会建到别的 cwd 之下；运行期间可用 `chbase <新路径>` 改，但仅对当前进程有效

<!-- 20260918-038 -->

## VES 未捕获的异常会先把 traceback 写到 trac…

VES 未捕获的异常会先把 traceback 写到 `traceback/[%Y-%m-%d-%H-%M-%S]_Traceback.txt`（相对 cwd，父目录不存在则自动创建）再向上抛；这是排查 VES 内部异常的第一现场，`〈项目目录〉/Python/VES/traceback/` 下已有实例文件
