# 第七章｜亲手搭一个 HelloAgents

前面几章主要在理解和使用 Agent；这一章开始自己定义消息、配置、模型接口、工具和不同 Agent 的控制流。代码集中在 [HelloAgents 独立项目](./HelloAgents/README.md)，它有自己的 uv 环境与锁文件。

目前已经走到 **Plan-and-Solve** 和 **Function Calling**：除了 Simple、ReAct、Reflection，还能查看计划逐步执行，以及模型原生工具调用如何从 Schema 走到执行结果回填。第七章现有 24 个 `demo_*.py` 演示脚本，按“无需 API 的基础模块 → 需要模型的 Agent 流程”阅读更顺畅。

## 最短上手路径

```powershell
# 从仓库根目录进入独立项目
cd ".\第七章\HelloAgents"
uv sync
uv run python -m demos.demo_message
uv run python -m demos.demo_calculator
uv run python -m demos.demo_tool_schema
```

进一步的代码地图、示例选择、模型配置和当前功能边界都写在 [HelloAgents 项目 README](./HelloAgents/README.md)。目前本章还没有单独的课后题笔记；代码注释和演示是这一阶段的主要记录。

[返回主页](../README.md)
