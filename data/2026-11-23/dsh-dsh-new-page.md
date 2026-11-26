<!-- 20261123-007 -->

## dsh-new-page 0.6.1（commit 7e7f41…

dsh-new-page 0.6.1（commit 7e7f414）修复 np_screenshot 报 "the page did not report its rectangle in time"：根因是矩形请求只发给 activeClientId（最近 hello 的客户端），当该窗口已关闭或停止轮询时，活着的窗口永远收不到 → 超时；

同时 np_exec 也会 no-client。

### 修复

①矩形请求广播给所有在线轮询客户端（幂等，客户端按 id 去重，第一个 /rect 应答解析 waiter 并从 pending 移除）；②活跃客户端没有任何打开的 poller 且静默超过 4 秒时，下一个轮询客户端接管 job-claim 角色（adoptClientIfStale），避免死窗口卡住 exec；

③矩形改为 iframe 与所有 overflow/clipPath 裁剪祖先及视口的交集——固定视口 1280×820 的页面在 913 宽侧栏里曾把聊天列带进截图，现在只截可见页面（913×820）。

### 复验

重启后 np_exec np-23 成功、np_screenshot np-23 → 913×820 只含页面。测试 host 20 / proxy 15 / env 15 / pool 13 全绿。

<!-- 20261123-008 -->

## dsh-new-page 0.7.0 让 np_screensh…

dsh-new-page 0.7.0 让 np_screenshot 截到被挡住/不可见的部分：窗口级 GDI 捕获只能拿到窗口里真实绘制过的像素，被 DSH 自己的 UI 裁掉、标签页收起或窗口外滚动的部分没有像素。

### 新增离屏渲染路径

Host 通过 rect 通道的 snapshot:true 向页面要 DOM 快照（客户端把 POST /dsh-new-page/snapshot 交给 Host），桥接在消息处理里延迟到下一帧再序列化：克隆 documentElement、删掉所有 script、把每个 canvas 用 toDataURL 换成 img（下一帧取，WebGL 的绘制缓冲还没被清，能截到 3D 画面），带 base/width/height/scrollHeight/dpr。

Host 写临时 HTML，用系统 Edge/Chrome 的 --headless=new --screenshot --window-size=W×scrollHeight --virtual-time-budget=6000 --force-device-scale-factor=1 渲染成 PNG，串行执行、用完删临时文件；

宽高上限 3000 万像素。工具行为：默认窗口捕获；一旦 clipped=true 或标签页不可见就自动改用离屏渲染（mode=offscreen、fullPage=true），offscreen:true 可强制；fullPage 在可见标签页上仍用滚动拼接。

实测 LIFE³（WebGL 3D）默认截图被侧栏裁切 → 自动离屏 1280×820，3D 细胞画面与统计（59 代/3742 细胞）完整；显式 offscreen 同样 1280×820。

### 限制

离屏不重放动画/视频帧（脚本被移除、DOM 冻结），需要本机有 Edge/Chrome。测试 host 20 / proxy 15 / env 15 / pool 13 全绿。
