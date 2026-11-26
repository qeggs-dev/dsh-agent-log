<!-- 20261126-002 -->

## 待办（功能基本完成后）

优化 UI 并引入 i18n/多语言框架。当前 Web UI 与 Android 壳的文案是中文硬编码；i18n 需要覆盖 Web UI（index.html/app.js 的文案、notice/tool 标签、日期/数字格式）、Android 壳（通知、权限/错误提示），以及可能的 agent 输出语言策略。优先级：功能收尾后再做，不在 3a/3b 阶段插入；先保证字符串集中化，避免散落在 DOM/JS 里，为后续框架（如 i18next 或轻量 JSON 字典）留出结构。
