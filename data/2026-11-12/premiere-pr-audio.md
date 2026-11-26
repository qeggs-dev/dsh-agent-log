<!-- 20261112-021 -->

## Pr 2020 的 VST3 宿主会拒绝用 `juce::AudioProcessorValueTreeState`（APVTS）构建参数的插件

，而且不给任何错误提示——插件管理器里只显示「工作不正常」，同时把 DLL 路径写进 `%APPDATA%\Adobe\Premiere Pro\14.0\DynamicAudioPlugInBlacklist.xml`。

### 二分实测排除项

JUCE 9 / VST3 SDK 3.8、分类字符串 `Fx|Pitch Shift`、真实编辑器、Signalsmith core、bypass 参数、延迟上报、DSP 处理路径、tail 长度、choice 参数**都不是原因**；

改成裸 `AudioParameterFloat/Choice/Bool` + 手写 ValueTree 状态序列化后**立即通过**。

### 结论

JUCE 项目若目标宿主包含老版 Pr，参数层不要用 APVTS。

Ghidra 旁证：Pr 在 `dvaaudiofilterhost.dll` 的 `VST3AudioFilter` 构造里，组件创建/初始化/取 `IAudioProcessor` 任一失败就抛 `Could not create component` 并拉黑。

修复后的 `PR Stretch.vst3` SHA256 `4E0F3F85…78ECA64B`，在效果面板里位于 `VST3 → 变调 → pr-audio → PR Stretch`。

<!-- 20261112-022 -->

## Pr 的 CEP manifest 里**宿主标识必须是 `PP…

Pr 的 CEP manifest 里**宿主标识必须是 `PPRO`，不是 `PR`**：写 `<Host Name="PR">` 会被 PlugPlug 判为「不支持本宿主」静默跳过，整项「窗口 → 扩展」变灰（菜单项存在但不可点）。

Pr 2020 使用 CEP 9，调试模式键是 `HKCU\SOFTWARE\Adobe\CSXS.9\PlayerDebugMode = "1"`（字符串型，同时写 .10/.11/.12 更保险），扩展装在 `%APPDATA%\Adobe\CEP\extensions\<BundleId>\`。

另外本机 **火绒会拦截 Pr 的音频硬件初始化**，表现为每次启动弹「MME 设备内部错误」，此时 Pr 没有可用音频输出、做不了听感测试（火绒放行后仍需重启 Pr）。

<!-- 20261112-023 -->

## `PR Stretch.vst3` 在 Pr 2020 里真正跑…

`PR Stretch.vst3` 在 Pr 2020 里真正跑通的最终形态是 **无自定义编辑器版本**（v1，SHA256 `03A64976…B1603716`）：`hasEditor()=false`、`createEditor()` 返回 nullptr，其余全部保留（5 个裸参数、Signalsmith core、F0 检测、预延迟、延迟上报 3456、`processBlockBypassed`、手写 ValueTree 状态序列化、tail 0.25）。

参数在 Pr 的「效果控件 → 各个参数」里直接调，可画关键帧。

**自定义编辑器 `PrAudioStretchEditor` 会让 Pr 2020 一实例化就崩**：Frida 抓到 `access-violation read at 0x0`，`rip=MSVCP140.dll+0x18c34`（C++ 标准异常抛出辅助函数），调用栈全部落在插件模块内（`PR Stretch.vst3+0x20f7f7` 等），宿主侧为 `dvaaudiofilterhost.dll → AudioFilterHost.dll`。

### 二分验证

C1（关编辑器）可用；C2（关延迟上报）、C3（关 DSP）都带编辑器、都崩；C1+C3 叠加、C2+C3 叠加均失败。

### 结论

**编辑器是唯一变量，与延迟上报、DSP、参数、状态序列化无关**。嫌疑指向 `ParameterAttachment` / `SliderParameterAttachment` 的 `sendInitialUpdate()` 异步回调（可能对空 `std::function` 调用）。
