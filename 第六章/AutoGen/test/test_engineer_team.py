import asyncio
from pathlib import Path

from autogen_agentchat.agents import CodeExecutorAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor

# 复用 OpenAiClient1.py 里面已经写好的函数
from OpenAiClient import create_openai_model_client, create_engineer
'''
上一关，由我们自己充当传话员
engineer_response = await engineer.on_messages(...)
executor_response = await code_executor_agent.on_messages(
    [engineer_response.chat_message],
    ...
)

流程为：
Engineer
   ↓
你的 Python 代码手动拿结果
   ↓
你的 Python 代码手动传给 Executor
   ↓
CodeExecutor
'''

async def main():
    # =========================================================
    # 1. 创建大模型客户端
    # =========================================================
    model_client = create_openai_model_client()

    # =========================================================
    # 2. 创建真正的 Engineer Agent
    # =========================================================
    engineer = create_engineer(model_client)

    # =========================================================
    # 3. 创建 Docker 工作目录
    # =========================================================
    work_dir = Path("../agent_workspace")
    work_dir.mkdir(exist_ok=True)

    try:
        # =====================================================
        # 4. 创建 Docker 代码执行器
        # =====================================================
        # 决定下一个轮到谁说话；维护并传递整个团队的消息上下文，更像是维护一个共同的“消息线程”
        async with DockerCommandLineCodeExecutor(
            image="python:3.12-slim",
            work_dir=work_dir,
            timeout=30,
        ) as docker_executor:

            # =================================================
            # 5. 创建 CodeExecutorAgent
            # =================================================
            code_executor = CodeExecutorAgent(
                name="CodeExecutor",

                # 真正执行代码的是 Docker Executor
                code_executor=docker_executor,

                # 只执行 Engineer 发出的代码
                sources=["Engineer"],
            )

            # =================================================
            # 6. 创建两人团队，消息自动广播给团队
            # =================================================
            team = RoundRobinGroupChat(
                participants=[
                    engineer,
                    code_executor,
                ],

                # 只运行两轮：
                # 第 1 轮 Engineer
                # 第 2 轮 CodeExecutor
                max_turns=2,
            )

            # =================================================
            # 7. 给整个团队一个任务
            # =================================================
            task = """
请编写一个 Python 程序：

计算 1 到 100 所有整数的和，并打印最终结果。

要求：
1. 使用 Python
2. 给出完整可运行代码
3. 代码必须放在一个完整的 ```python ... ``` Markdown 代码块中
4. 不需要解释代码
"""

            # =================================================
            # 8. 启动整个团队
            # =================================================
            result = await Console(
                team.run_stream(task=task)
            )

            # =================================================
            # 9. 查看团队为什么停止
            # =================================================
            print("\n" + "=" * 60)
            print("团队停止原因：")
            print(result.stop_reason)

    finally:
        # =====================================================
        # 10. 关闭大模型客户端
        # =====================================================
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())