# HelloAgents｜从零搭建的 Agent 练习框架

这是[第七章](../README.md)的独立 uv 项目。目标是把 Agent 看成一组可读、可替换的部件：消息格式、模型客户端、工具描述、工具执行和几种不同的控制流。这里的代码优先服务于学习与实验，而不是声称已经具备生产级完整性。

> 这不是一个“一键造出万能 Agent”的黑盒。我更想留下每次接口演进的原因：为什么消息需要统一格式？为什么工具要告诉模型参数长什么样？为什么模型决定调用工具后，程序还必须负责真正执行？

## 一个请求怎样走完整条链

用户提出问题后，`Message` 保存输入；`Agent` 决定当前用哪种控制流；`HelloAgentsLLM` 与模型通信。若模型发出 `tool_call`，程序从工具 Schema 对应的对象里解析参数、调用工具，把结果作为 `tool` 消息送回模型；模型再决定给出答案还是继续调用工具。`FunctionCallAgent` 已把这个过程写成最多 `max_steps` 轮的循环。这里的关键是**模型提出请求，Python 程序执行动作**，两者不能混为一谈。

## 代码地图

| 目录 | 内容 |
|---|---|
| [`hello_agents/core/`](./hello_agents/core/) | `Message`、`Config`、`HelloAgentsLLM`、`Agent` 基类 |
| [`hello_agents/tools/`](./hello_agents/tools/) | `ToolParameter`、`BaseTool`、`ToolRegistry`、`CalculatorTool`、普通函数计算器、多源搜索 |
| [`hello_agents/agents/`](./hello_agents/agents/) | `SimpleAgent`、`ReActAgent`、`ReflectionAgent`、`PlanAndSolveAgent`、`FunctionCallAgent` |
| [`demos/`](./demos/) | 33 个阶段性演示，包含历史接口探索；并非每个脚本都适合直接运行 |

`BaseTool.to_openai_schema()` 把工具的参数说明转换为模型 API 可读的 Schema；`FunctionCallAgent` 再把模型给出的 JSON 参数解析、转换，找到工具执行，并把结果作为 `tool` 消息回传。另一条路线是 `ToolRegistry.register_function()`：普通的 Python 函数无需先写成工具类，也能通过名字和描述接入注册表。目前这两条路线服务于不同的教学场景，不应误以为普通函数会自动获得 Function Calling Schema。

## 先运行

在当前目录使用 PowerShell：

```powershell
uv sync
$env:PYTHONUTF8 = "1" # Windows 中文输出乱码时可保留
uv run python -m demos.demo_message
uv run python -m demos.demo_calculator
uv run python -m demos.demo_tool_schema
uv run python -m demos.demo_registry_function
uv run python -m demos.demo_custom_calculator
```

这些基础演示不需要模型 API；它们适合在还没有密钥时先理解“工具对象”和“普通函数工具”的区别。需要模型时，把仓库根目录的模板复制到**本目录**，并填入你自己的 OpenAI 兼容服务配置：

```powershell
Copy-Item ".\..\..\.env.example" ".\.env"
# 编辑 .env 中的 LLM_API_KEY、LLM_MODEL_ID、LLM_BASE_URL
uv run python -m demos.demo_simple_agent
```

真实 `.env` 不应提交。不同服务对 `tools` 的支持不同；Function Calling 示例要求服务支持原生工具调用。

搜索实验还需按需配置 `TAVILY_API_KEY` / `SERPAPI_API_KEY`。只有同时存在可用搜索源时，才能观察“首选源失败后尝试下一个源”的回退；没有密钥时，脚本只会报告没有可用搜索源。

## 演示怎么选

| 想看什么 | 建议运行 | 是否需要模型 API |
|---|---|---|
| 消息、配置、工具和 Schema | `demo_message`、`demo_config`、`demo_calculator`、`demo_registry`、`demo_tool_parameter`、`demo_tool_schema` | 否 |
| 普通函数工具与兼容接口 | `demo_registry_function`、`demo_custom_calculator`、`demo_registry_compat` | 否 |
| 参数转换与 Agent 基类 | `demo_parameter_conversion`、`demo_agent` | 需模型配置；这两个示例本身主要演示本地逻辑 |
| 模型客户端 | `demo_llm` | 是 |
| 普通对话与 ReAct | `demo_simple_agent`、`demo_react` | 是 |
| 计划与逐步执行 | `demo_plan_solve_v1`、`demo_plan_solve_v2`、`demo_plan_solve_custom` | 是 |
| 一轮反思 | `demo_reflection` | 是 |
| 原生 Function Calling 分步学习 | `demo_function_call_v1`～`v3`、`demo_function_call_agent_v1`～`v4` | 是 |
| 当前 FunctionCallAgent 流程 | `demo_function_call_agent_run`、`demo_function_call_agent_loop` | 是，且服务需支持 `tools`；多轮场景仍待完整验证 |
| 多源搜索与回退 | `demo_search_sources`、`demo_search_fallback`、`demo_advanced_search_registry` | 需要相应搜索服务与密钥，部分场景需两个源 |

命令格式统一为 `uv run python -m demos.<上表名称>`。例如：

```powershell
uv run python -m demos.demo_plan_solve_v2
uv run python -m demos.demo_reflection
uv run python -m demos.demo_function_call_agent_run
```

`demo_tool_base` 是较早的基类探索脚本；当前 `BaseTool` 已新增必须实现的 `get_parameters()`，因此它不能作为可直接运行的入口。`demo_tool_run_compat` 故意传入缺失参数，当前会抛异常，适合读代码理解接口边界，不适合当作“全部通过”的演示。`demo_function_call_agent_v1`～`v4` 是分步学习记录，实际控制流请看 `demo_function_call_agent_run` 和 `demo_function_call_agent_loop`。

## 工具系统最近新增了什么

- **函数也能成为工具**：`my_calculator.py` 把 `my_calculate()` 交给 `ToolRegistry.register_function()`；`demo_custom_calculator.py` 用无需模型的算式把这条链跑一遍。
- **旧接口仍可对照**：`CalculatorTool.execute("2+3")` 与 `CalculatorTool.run({"expression": "2+3"})` 并存，`demo_registry_compat.py` 展示两种调用方式。
- **搜索可以尝试后备源**：`advanced_search.py` 检查 Tavily / SerpApi 是否可用，按顺序尝试，首选源抛错时转向下一个；`demo_search_fallback.py` 用模拟 Tavily 故障观察这条分支。
- **注册表统一描述**：类工具与普通函数的说明都能出现在 `get_tools_description()` 中，供 ReAct 提示词使用。当前 `list_tools()` 只列类工具，读代码时不要把它误当成全部已注册工具列表。

## 当前边界与下一步

- `PlanAndSolveAgent` 先生成计划列表，再依次执行；尚无动态重规划或步骤失败恢复。
- `ReflectionAgent` 做一次反馈检查，必要时改写一次；尚非多轮反思循环。
- `FunctionCallAgent` 已有受 `max_steps` 限制的多轮循环，能处理一轮响应里的多个工具请求；但端到端模型调用、轮数耗尽后的返回路径仍需验证和完善。`BaseTool.run()` 的兼容层目前只支持单参数工具。
- 搜索回退只在已配置且可用的源之间尝试；服务限流、错误内容和结果质量仍需人工检查。普通函数工具当前只接受字符串参数。
- 对话历史有基础保存能力，但这些教学演示不等于并发、持久化、权限与安全性验证。

如果要继续扩展，我会优先考虑更完整的工具参数映射、多轮循环异常路径、错误恢复，以及可重复的离线测试。现阶段最值得做的事是先读懂每一层的输入、输出和状态变化。

[返回第七章](../README.md) · [返回主页](../../README.md)
