# 编码提示词：实现新模块

> 用途：指导 AI 实现一个新的模块

---

## 提示词模板

```
请阅读 memory-bank/ 目录下的所有文档，了解项目架构和当前进度。

然后实现以下模块：

## 模块信息

- 模块名称：{module_name}
- 所属层级：{layer}
- 功能描述：{description}

## 参考代码

以下项目已有类似实现，请参考：

- 来源：{source_project}
- 文件：{source_file}
- 复用程度：{reuse_level}

## 实现要求

1. 先定义数据模型（使用 dataclass）
2. 再定义接口/抽象类
3. 最后实现具体逻辑
4. 添加类型注解
5. 编写简单的测试用例

## 输出位置

- 文件：{output_file}
- 目录：{output_dir}

## 验证方式

{verification_method}

---

开始前请确认：
1. 你已阅读 ARCHITECTURE.md
2. 你已阅读 PROGRESS.md
3. 你了解这个模块与其他模块的关系

完成后请更新 PROGRESS.md。
```

---

## 示例：实现时间沙箱

```
请阅读 memory-bank/ 目录下的所有文档，了解项目架构和当前进度。

然后实现以下模块：

## 模块信息

- 模块名称：TimeSandbox
- 所属层级：第二层：世界观与宏观法则层
- 功能描述：管理全局时间轴、推进时间、触发事件、支持回溯

## 参考代码

以下项目已有类似实现，请参考：

- 来源：Strategos
- 文件：strategos-reference/core/time.py, core/events.py, core/event_store.py
- 复用程度：高，可直接复制并扩展

## 实现要求

1. 先定义数据模型（使用 dataclass）
   - TimeSandboxEvent（扩展 NarrativeNode）
   - TimeSandboxState
2. 再定义接口/抽象类
   - ITimeSandbox
3. 最后实现具体逻辑
   - TimeSandbox 类
4. 添加类型注解
5. 编写简单的测试用例
   - 测试时间推进
   - 测试事件触发
   - 测试时间回溯

## 输出位置

- 文件：time_sandbox.py
- 目录：src/world/

## 验证方式

运行测试：
```python
sandbox = TimeSandbox()
await sandbox.start()
await sandbox.advance(timedelta(hours=1))
assert sandbox.get_time() == 3600
```

---

开始前请确认：
1. 你已阅读 ARCHITECTURE.md
2. 你已阅读 PROGRESS.md
3. 你了解这个模块与其他模块的关系

完成后请更新 PROGRESS.md。
```