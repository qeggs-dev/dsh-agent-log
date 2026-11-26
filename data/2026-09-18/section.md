<!-- 20260918-041 -->

## 决策

操作手台改用工作区根 `.venv`（Python 3.11.9），弃用 VES 的 `envs\net\.venv`（Python 3.14.3）；`console.bat` 的 `PY` 变量与提示语同步改指 `.venv`。

### 理由

根 `.venv` 是标准布局、编辑器与其他工具可直接识别、不依赖 VES；实测手台在 3.11 下 libs/selftest/req 全部正常，且 `import orjson+httpx+pydantic` 反而更快（858ms vs 941ms），换环境无性能代价；

注意换环境**不解决**手台自身的固定开销与输出回声问题（见 20260918-042）
