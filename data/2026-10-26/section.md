<!-- 20261026-008 -->

## 子代理接缝的权限机制（本次读 0.2.1-rc.3 的 dsh-subagent/lib/index.js 实测得出，做同类插件必须知道）

①manager 在「未发布的创建窗口」里调 `captureDelegatedPolicyOverrides(parent)` → `appendDelegatedPolicyOverrides(childSession)`，写入 `sandbox/mode`（只取父会话的**显式 override**，不取部署默认）+ `approval/policy: never` + 视情况 `permission/preset`，事件都带 `source: 'delegation'`；

**这些事件在 provider 返回的 seed 之后追加**（源码注释明说 "fresh policy wins stale seed state"），所以**用 `prepareContinuable` 的 seed 无法把子会话改得比父会话更窄**——第一次实现就是这样被覆盖的（子会话日志里 seed 的 read-only 后面紧跟 delegation 的 danger-full-access）。

②可行窗口是 `session/created`：它同样在创建窗口内、且在 delegation 事件之后、prompt 与 `turn/start` 之前，因此在这里 append 的权限事件能保证第一轮就生效；

`permission-presets` 自己也在这个事件上做 `pinInitialPermission`。

③manager 对 delegated 子代理**无条件把 approval 钉成 never**，且 `permissionPreset` 只在父会话预设是 `auto` / `danger-full-access` 时才继承。

④`ctx.subagents.resolveMaxDepth()` 默认返回 1，所以子代理再派子代理会报 `subagent depth 2 exceeds maxDepth 1`——这也是为什么「父会话降权后子会话再越权派生」在当前默认配置下实际不可达（兜底监听器仍保留）。

⑤`ctx.agents.create({sessionId, parentAgent, seed, meta})` 是另一条完全绕开 manager 的建会话路径（`meta` 可设 parentSession/origin/delegationDepth/agentPreset），但那样建的会话不进 subagent 目录，`send_message` / `list_agents` 也认不到它。
