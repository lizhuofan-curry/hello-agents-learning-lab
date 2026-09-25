# 第六章｜多个 Agent 如何协作

这一章不追求“哪个框架最好”，而是把协作机制拆开看：谁负责下一轮发言？消息如何传递？任务失败后能不能回退？质量检查由谁做？四组实验分别从不同角度回答这些问题。

| 框架 | 当前目录内容 | 入门入口 | uv 分组 |
|---|---|---|---|
| AutoGen | 软件开发团队、代码执行与测试相关实验 | [OpenAiClient1.py](./AutoGen/OpenAiClient1.py) | `autogen` |
| AgentScope | 单 Agent、双 Agent、MsgHub、串行/扇出流程、结构化输出六步 | [step1_single_agent.py](./AgentScope/step1_single_agent.py) | `agentscope` |
| CAMEL | 角色扮演协作、心理书与 BCI 学习计划示例 | [BCI学习计划.py](./Camel/BCI学习计划.py) | `camel` |
| LangGraph | 从基础图到路由、工具调用、反思和完整 Agent 的分步实验 | [step1_basic_graph.py](./LangGraph/step1_basic_graph.py) | `langgraph` |

建议先运行不依赖模型的 LangGraph 基础图，再选择一个框架深入：

```powershell
# 在仓库根目录
uv sync --group langgraph
uv run --group langgraph python ".\第六章\LangGraph\step1_basic_graph.py"
```

其他框架按表中分组执行 `uv sync --group <分组>` 和 `uv run --group <分组> python <脚本路径>`。需要模型的示例先用根目录 `.env.example` 建立 `.env` 并填写服务配置。AutoGen 的代码执行与 Docker 示例可能运行生成的代码或依赖 Docker；阅读脚本、核对工作目录和执行权限后再尝试，勿在存有敏感数据的环境中直接运行。仓库中的 `agent_workspace` / `docker_workspace` 是生成物路径，不是章节教程入口。

[第六章课后习题](../notes/第六章/第六章的问题.md)记录了框架对比、动态回退、QA、消息驱动架构与多 Agent 分歧处理。这里的案例是学习实验，不等于生产环境的可靠性验证。

[返回主页](../README.md) · [下一站：自制 HelloAgents](../第七章/README.md)
