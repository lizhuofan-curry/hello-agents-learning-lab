# 第四章｜Agent 怎样安排“想”和“做”

同样是完成一个任务，ReAct、Plan-and-Solve 和 Reflection 的控制方式很不一样：一个边观察边行动，一个先列计划再执行，一个先给答案再自查。这里保留了独立脚本，方便对照提示词、状态和终止条件。

> 想象同一道复杂题交给三位同学：一位做一步就查一次资料，一位先写出完整计划，一位交卷前反复自查。本章要看的正是这三种“组织思考”的办法。

## 三种范式放在一张桌上

| 范式 | 核心节奏 | 适合观察的现象 |
|---|---|---|
| ReAct | 想一步 → 用工具 → 看结果 → 再决定 | 外部事实能否及时改变下一步 |
| Plan-and-Solve | 先规划 → 按步骤执行 | 计划如何约束执行、错误怎样传递 |
| Reflection | 初稿 → 评价 → 修改 | 反馈能否真正改进答案，而不是空泛自夸 |

它们不是“谁取代谁”。同一个任务也可能先规划，再用 ReAct 执行其中一步，最后做 Reflection；但这三个独立示例还没有被包装成这种完整组合。

| 路线 | 代码入口 | 读代码时可以问 |
|---|---|---|
| ReAct | [Hello_Agent.py](./ReAct/Hello_Agent.py)、[ReAct_Agent.py](./ReAct/ReAct_Agent.py) | 工具结果如何回到下一步推理？ |
| Plan-and-Solve | [PlanAndSolveAgent.py](./Plan-and-Solve/PlanAndSolveAgent.py)、[Plan.py](./Plan-and-Solve/Plan.py)、[Executor.py](./Plan-and-Solve/Executor.py) | 计划与执行怎样分工？ |
| Reflection | [ReflectionAgent.py](./Reflection/ReflectionAgent.py)、[Memory.py](./Reflection/Memory.py) | 反馈怎样影响改写？何时停止？该脚本设置最多 3 轮 |

推荐阅读顺序：先看 `ReAct/React_v0.py` 中的工具调用骨架，再看 `ReAct/ReAct_Agent.py` 的循环；之后到 `Plan-and-Solve/` 对照 Planner 与 Executor，最后看 Reflection 怎样保留初稿和反馈。每切换一个范式，都追问“谁决定下一步”。

在仓库根目录：

```powershell
uv sync --group chapter4
Copy-Item .env.example .env
# 编辑 .env，填写模型服务；部分 ReAct 搜索示例还需 SERPAPI_API_KEY
uv run --group chapter4 python ".\第四章\Plan-and-Solve\PlanAndSolveAgent.py"
```

这些脚本会调用模型；不同示例可能还依赖搜索服务。建议先看每个入口文件的 `__main__` 示例输入，再运行，避免意外的 API 消耗。这里是学习三种范式的独立实现，和第七章逐渐模块化的自制框架不是同一个项目。

## 把同一个问题交给三种方法

试着提出“规划一次两天的旅行，先查天气，再按天气调整安排”。预测三种范式会在什么时间点发现天气变化：ReAct 可以在行动之后调整；Plan-and-Solve 取决于计划和执行器如何传递结果；Reflection 更适合检查计划是否合理。先把预测写下来，再读代码或运行对照，比单纯背定义更容易记住差别。

注意第四章的 Reflection 脚本是带 `max_iterations` 的独立实验；[第七章的 `ReflectionAgent`](../第七章/HelloAgents/README.md) 当前只有一轮反思，两个同名概念不能混为同一实现。

[第四章课后习题](../notes/第四章/第四章的问题.md)进一步讨论解析脆弱性、动态重规划、反思终止、混合范式和上线风险。

[返回主页](../README.md) · [下一站：多智能体框架](../第六章/README.md)
