# 第六章｜多个 Agent 如何协作

这一章不追求“哪个框架最好”，而是把协作机制拆开看：谁负责下一轮发言？消息如何传递？任务失败后能不能回退？质量检查由谁做？四组实验分别从不同角度回答这些问题。

> 多 Agent 并不等于“多开几个聊天窗口”。真正难的是分工、交接、回退与停止：谁有权说下一句？工具结果归谁处理？发生分歧时，工作还能不能往前走？

## 四种框架，各看一个问题

| 框架 | 当前目录内容 | 入门入口 | uv 分组 |
|---|---|---|---|
| AutoGen | 软件开发团队、代码执行与测试相关实验 | [OpenAiClient1.py](./AutoGen/OpenAiClient1.py) | `autogen` |
| AgentScope | 单 Agent、双 Agent、MsgHub、串行/扇出流程、结构化输出六步 | [step1_single_agent.py](./AgentScope/step1_single_agent.py) | `agentscope` |
| CAMEL | 角色扮演协作、心理书与 BCI 学习计划示例 | [BCI学习计划.py](./Camel/BCI学习计划.py) | `camel` |
| LangGraph | 从基础图到路由、工具调用、反思和完整 Agent 的分步实验 | [step1_basic_graph.py](./LangGraph/step1_basic_graph.py) | `langgraph` |

- **AutoGen**：关注角色轮流发言与代码执行器怎样进入协作链；部分案例还涉及 Streamlit 页面与测试。
- **AgentScope**：从单 Agent 走到 MsgHub，再到串行、扇出与结构化输出，观察“消息到了”和“轮到我回答”为什么要分开。
- **CAMEL**：看角色扮演式双 Agent 如何围绕写作或 BCI 学习计划相互推进。
- **LangGraph**：从 `State` 和节点连线开始，一步步加条件路由、记忆、工具和反思；目录里保留了 `step1` 到 `step12` 的演进。

建议先运行不依赖模型的 LangGraph 基础图，再选择一个框架深入：

```powershell
# 在仓库根目录
uv sync --group langgraph
uv run --group langgraph python ".\第六章\LangGraph\step1_basic_graph.py"
```

其他框架按表中分组执行 `uv sync --group <分组>` 和 `uv run --group <分组> python <脚本路径>`。需要模型的示例先用根目录 `.env.example` 建立 `.env` 并填写服务配置。AutoGen 的代码执行与 Docker 示例可能运行生成的代码或依赖 Docker；阅读脚本、核对工作目录和执行权限后再尝试，勿在存有敏感数据的环境中直接运行。仓库中的 `agent_workspace` / `docker_workspace` 是生成物路径，不是章节教程入口。

## 推荐的阅读路线

先用 LangGraph 的基础图看清“节点、边、状态”；再读 AgentScope 的 `step1`～`step3` 理解消息交接；最后选择 AutoGen 或 CAMEL 看团队协作。每一步都画一个最简单的消息流：**谁产生消息 → 谁能看到 → 谁决定下一步 → 何时结束**。这样再遇到新的框架，也能用同一套问题拆解它。

可以做一个小对照：假设“搜索 Agent 给错了网页”，四个示例分别在哪里插入复查？第六章笔记中的质量监控与动态回退讨论，就是从这个问题延伸出来的设计练习；它们并不意味着这些仓库脚本已实现完整的生产级回退系统。

[第六章课后习题](../notes/第六章/第六章的问题.md)记录了框架对比、动态回退、QA、消息驱动架构与多 Agent 分歧处理。这里的案例是学习实验，不等于生产环境的可靠性验证。

[返回主页](../README.md) · [下一站：自制 HelloAgents](../第七章/README.md)
