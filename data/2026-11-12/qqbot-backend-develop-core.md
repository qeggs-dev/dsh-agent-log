<!-- 20261112-015 -->

## Backend/develop/core 的请求驱动现状（202…

Backend/develop/core 的请求驱动现状（2026-11-12 实读代码，非推测）：
①**第二个入口已经存在且是复制品**——`tool_caller/tools/sub_agent.py` 共 330 行，把 Core.chat 的中段（取模型 / 合并 tool 白名单 / 构造 Request / 起 ModelRequester / 解析输出）手工重抄约 180 行；它还带 continuous_run，用 `await runtime.input.wait()` 自建常驻循环，即一个工具自己实现了一个回合的生命周期，但这个「回合」没有 turn id、没有状态栈、没有请求日志、不存上下文。
②`fastapi_request` 全项目 18 处引用，**真实用途只有 1 处**：`core/image/parse_response.py:37` 的 `url_for("files.generated_image")` 拼生成图绝对 URL，其余 17 处全是搬运链 chat → ModelRequester → ToolsCaller → RuntimePackage。
③`pools/awaitable_pool/task_pool.py` 的 run_task 是「create_task 后 await」的等待器，不是队列；同一对象兼任并发闸门（Semaphore）与 break 的取消索引。
④流式消费端 `model_requester/_caller.py:68` 是 `wait_for(queue.get(), 10)` 连续失败 5 次就静默 break——慢 50 秒等于流无声结束、客户端以为正常完成，是用户自己那条「不允许静默生效或静默失效」纪律的反例。
⑤全项目没有任何事件总线 / 发布订阅抽象；唯一异步面是 `GET /generate/chat/buffer/{user_id}` 读 content_buffers_pools。
⑥版本号不一致：pyproject.toml 是 4.9.11.0，core/_info.py 是 4.10.14.0。
