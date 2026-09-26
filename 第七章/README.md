# 第七章｜亲手搭一个 HelloAgents

前面几章主要在理解和使用 Agent；这一章开始自己定义消息、配置、模型接口、工具和不同 Agent 的控制流。代码集中在 [HelloAgents 独立项目](./HelloAgents/README.md)，它有自己的 uv 环境与锁文件。

> 从“会用框架”到“能解释框架”：如果工具只有 `execute()`，模型如何知道它需要什么参数？如果搜索源宕了，Agent 为什么不能直接停在报错上？这一章把这些问题一个个变成代码。

目前已经走到 **Plan-and-Solve、Function Calling、普通函数工具注册与多源搜索回退**。第七章现有 33 个 `demo_*.py` 阶段性演示脚本；推荐按“无需 API 的基础模块 → Agent 控制流 → 需要搜索服务的工具实验”阅读，而不是把所有历史脚本一次运行。

## 目前的搭建顺序

| 阶段 | 我做了什么 | 最值得看的入口 |
|---|---|---|
| 先约定语言 | `Message`、`Config`、模型客户端与 `Agent` 基类 | [core 目录](./HelloAgents/hello_agents/core/) |
| 让 Agent 有手 | 计算器、工具参数、Schema、注册表 | [tools 目录](./HelloAgents/hello_agents/tools/) |
| 给行动加节奏 | Simple、ReAct、Reflection、Plan-and-Solve | [agents 目录](./HelloAgents/hello_agents/agents/) |
| 接上原生工具调用 | Function Calling 参数解析与受轮数限制的工具循环 | [项目演示索引](./HelloAgents/README.md#演示怎么选) |
| 增强工具系统 | 函数注册、Tavily/SerpApi 多源搜索与 fallback | [搜索工具代码](./HelloAgents/hello_agents/tools/advanced_search.py) |

这些能力处于不同成熟度：离线工具基础示例比较适合直接试跑；多轮 Function Calling 的控制流已写入代码，真实模型与异常路径还需要继续验证。章节 README 会明确区分这两件事。

## 最短上手路径

```powershell
# 从仓库根目录进入独立项目
cd ".\第七章\HelloAgents"
uv sync
uv run python -m demos.demo_message
uv run python -m demos.demo_calculator
uv run python -m demos.demo_tool_schema
uv run python -m demos.demo_registry_function
```

进一步的代码地图、示例选择、模型配置和当前功能边界都写在 [HelloAgents 项目 README](./HelloAgents/README.md)。目前本章还没有单独的课后题笔记；代码注释和演示是这一阶段的主要记录。

可以边看边问自己：一个工具究竟是普通 Python 函数、带 Schema 的对象，还是模型发起的一次 `tool_call`？它们不是同一个东西；把三者接起来，才构成真正的工具调用链。

[返回主页](../README.md)
