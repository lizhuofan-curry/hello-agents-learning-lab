# 第四章｜Agent 怎样安排“想”和“做”

同样是完成一个任务，ReAct、Plan-and-Solve 和 Reflection 的控制方式很不一样：一个边观察边行动，一个先列计划再执行，一个先给答案再自查。这里保留了独立脚本，方便对照提示词、状态和终止条件。

| 路线 | 代码入口 | 读代码时可以问 |
|---|---|---|
| ReAct | [Hello_Agent.py](./ReAct/Hello_Agent.py)、[ReAct_Agent.py](./ReAct/ReAct_Agent.py) | 工具结果如何回到下一步推理？ |
| Plan-and-Solve | [PlanAndSolveAgent.py](./Plan-and-Solve/PlanAndSolveAgent.py)、[Plan.py](./Plan-and-Solve/Plan.py)、[Executor.py](./Plan-and-Solve/Executor.py) | 计划与执行怎样分工？ |
| Reflection | [ReflectionAgent.py](./Reflection/ReflectionAgent.py)、[Memory.py](./Reflection/Memory.py) | 反馈怎样影响改写？何时停止？ |

在仓库根目录：

```powershell
uv sync --group chapter4
Copy-Item .env.example .env
# 编辑 .env，填写模型服务；部分 ReAct 搜索示例还需 SERPAPI_API_KEY
uv run --group chapter4 python ".\第四章\Plan-and-Solve\PlanAndSolveAgent.py"
```

这些脚本会调用模型；不同示例可能还依赖搜索服务。建议先看每个入口文件的 `__main__` 示例输入，再运行，避免意外的 API 消耗。这里是学习三种范式的独立实现，和第七章逐渐模块化的自制框架不是同一个项目。

[第四章课后习题](../notes/第四章/第四章的问题.md)进一步讨论解析脆弱性、动态重规划、反思终止、混合范式和上线风险。

[返回主页](../README.md) · [下一站：多智能体框架](../第六章/README.md)
