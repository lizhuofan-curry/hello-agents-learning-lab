# HelloAgents｜从零搭建的 Agent 练习框架

这是[第七章](../README.md)的独立 uv 项目。目标是把 Agent 看成一组可读、可替换的部件：消息格式、模型客户端、工具描述、工具执行和几种不同的控制流。这里的代码优先服务于学习与实验，而不是声称已经具备生产级完整性。

## 代码地图

| 目录 | 内容 |
|---|---|
| [`hello_agents/core/`](./hello_agents/core/) | `Message`、`Config`、`HelloAgentsLLM`、`Agent` 基类 |
| [`hello_agents/tools/`](./hello_agents/tools/) | `ToolParameter`、`BaseTool`、`ToolRegistry`、`CalculatorTool` |
| [`hello_agents/agents/`](./hello_agents/agents/) | `SimpleAgent`、`ReActAgent`、`ReflectionAgent`、`PlanAndSolveAgent`、`FunctionCallAgent` |
| [`demos/`](./demos/) | 24 个循序渐进的小实验 |

`BaseTool.to_openai_schema()` 把工具的参数说明转换为模型 API 可读的 Schema；`FunctionCallAgent` 再把模型给出的 JSON 参数解析、转换，找到工具执行，并把结果作为 `tool` 消息回传。这是本阶段最重要的连接点。

## 先运行

在当前目录使用 PowerShell：

```powershell
uv sync
$env:PYTHONUTF8 = "1" # Windows 中文输出乱码时可保留
uv run python -m demos.demo_message
uv run python -m demos.demo_calculator
uv run python -m demos.demo_tool_schema
```

这些基础演示不需要模型 API。需要模型时，把仓库根目录的模板复制到**本目录**，并填入你自己的 OpenAI 兼容服务配置：

```powershell
Copy-Item ".\..\..\.env.example" ".\.env"
# 编辑 .env 中的 LLM_API_KEY、LLM_MODEL_ID、LLM_BASE_URL
uv run python -m demos.demo_simple_agent
```

真实 `.env` 不应提交。不同服务对 `tools` 的支持不同；Function Calling 示例要求服务支持原生工具调用。

## 演示怎么选

| 想看什么 | 建议运行 | 是否需要模型 API |
|---|---|---|
| 消息、配置、工具和 Schema | `demo_message`、`demo_config`、`demo_calculator`、`demo_registry`、`demo_tool_parameter`、`demo_tool_schema` | 否 |
| 参数转换与 Agent 基类 | `demo_parameter_conversion`、`demo_agent` | 需模型配置；这两个示例本身主要演示本地逻辑 |
| 模型客户端 | `demo_llm` | 是 |
| 普通对话与 ReAct | `demo_simple_agent`、`demo_react` | 是 |
| 计划与逐步执行 | `demo_plan_solve_v1`、`demo_plan_solve_v2`、`demo_plan_solve_custom` | 是 |
| 一轮反思 | `demo_reflection` | 是 |
| 原生 Function Calling 分步学习 | `demo_function_call_v1`～`v3`、`demo_function_call_agent_v1`～`v4` | 是 |
| 完整的当前 FunctionCallAgent 示例 | `demo_function_call_agent_run` | 是，且服务需支持 `tools` |

命令格式统一为 `uv run python -m demos.<上表名称>`。例如：

```powershell
uv run python -m demos.demo_plan_solve_v2
uv run python -m demos.demo_reflection
uv run python -m demos.demo_function_call_agent_run
```

`demo_tool_base` 是较早的基类探索脚本；当前 `BaseTool` 已新增必须实现的 `get_parameters()`，所以不要把这个旧脚本当作可直接运行的入口。`demo_function_call_agent_v1`～`v4` 也是分步学习记录，完整入口以 `demo_function_call_agent_run` 为准。

## 当前边界与下一步

- `PlanAndSolveAgent` 先生成计划列表，再依次执行；尚无动态重规划或步骤失败恢复。
- `ReflectionAgent` 做一次反馈检查，必要时改写一次；尚非多轮反思循环。
- `FunctionCallAgent` 支持一次工具调用请求中执行工具、回填结果、再次请求模型；尚未循环处理第二次模型响应里的新工具请求，工具执行适配层当前只支持单参数工具。
- 对话历史有基础保存能力，但这些教学演示不等于并发、持久化、权限与安全性验证。

如果要继续扩展，我会优先考虑更完整的工具参数映射、多轮工具循环、错误恢复，以及可重复的离线测试。现阶段最值得做的事是先读懂每一层的输入、输出和状态变化。

[返回第七章](../README.md) · [返回主页](../../README.md)
