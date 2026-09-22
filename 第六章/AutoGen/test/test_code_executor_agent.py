import asyncio
from pathlib import Path

'''
模拟 Engineer 发代码
        ↓
CodeExecutorAgent 收到消息
        ↓
Docker 里真正运行
        ↓
把运行结果返回
'''
from autogen_core import CancellationToken
# 它的职责是找代码，执行代码，返回结果
from autogen_agentchat.agents import CodeExecutorAgent
# AutoGen中的Agent之间不是直接扔字符串，通常会封装成“消息对象”
from autogen_agentchat.messages import TextMessage
# 导入 Docker的执行器
#  Docker CommandLine Code Executor 基于 Docker 的命令行代码执行器
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor

async def main():
    # 1. 创建 Docker 工作目录
    work_dir = Path("../agent_workspace")
    work_dir.mkdir(exist_ok=True)

    # 2. 创建 Docker 代码执行器
    async with DockerCommandLineCodeExecutor(
        image="python:3.12-slim",
        work_dir=work_dir,
        timeout=30,
    ) as docker_executor:

        # 3. 创建 CodeExecutorAgent
        # 把 Agent 和 Docker Executor 连接起来
        code_executor_agent = CodeExecutorAgent(
            name="CodeExecutor",
            # 意思是CodeExecutorAgent，自己不负责真正跑代码，而是使用 Docker Executor运行
            code_executor=docker_executor,
            sources=["Engineer"],  # 只执行 Engineer发来的代码
        )

        # 4. 模拟 Engineer Agent 发来一条包含 Python 代码的消息
        engineer_message = TextMessage(
            content="""
Engineer 已经完成代码：

```python
print("Hello from Engineer!")

a = 10
b = 20

print("计算结果：", a + b)```
""",
            source="Engineer",)
        # 5. 把 Engineer 的消息交给 CodeExecutorAgent
        # 给 CodeExecutorAgent执行这些信息
        response = await code_executor_agent.on_messages(
            [engineer_message], # 因为可能一次收到多条信息，得到的是一个消息列表
            CancellationToken(),
        )

        # 6. 打印 Docker 执行后的返回结果
        print("CodeExecutorAgent 返回：")
        print(response.chat_message.content)

if __name__ == '__main__':
    asyncio.run(main())