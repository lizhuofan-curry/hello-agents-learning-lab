import asyncio
from pathlib import Path

from autogen_core import CancellationToken
from autogen_agentchat.agents import CodeExecutorAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor

# 直接复用你 OpenAiClient1.py 里面已经写好的两个函数
from OpenAiClient import create_openai_model_client, create_engineer


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
        # 4. 模拟“用户”向 Engineer 提出开发任务
        # =====================================================
        user_message = TextMessage(
            content="""
请编写一个简单的 Python 程序：

计算 1 到 100 所有整数的和，并打印结果。

要求：
1. 只使用 Python 标准库
2. 给出完整可运行代码
3. 必须把代码放在一个 ```python ... ``` Markdown 代码块中
""",
            source="user",
        )

        print("=" * 60)
        print("① 用户把任务交给 Engineer")
        print("=" * 60)

        # =====================================================
        # 5. 真正调用 Engineer Agent
        #    Engineer 会调用 LLM 自动生成代码
        # =====================================================
        engineer_response = await engineer.on_messages(
            [user_message],
            CancellationToken(),
        )

        print("\n" + "=" * 60)
        print("② Engineer 生成的回复")
        print("=" * 60)
        print(engineer_response.chat_message.content)

        # =====================================================
        # 6. 创建 Docker 执行器
        # =====================================================
        async with DockerCommandLineCodeExecutor(
            image="python:3.12-slim",
            work_dir=work_dir,
            timeout=30,
        ) as docker_executor:

            # =================================================
            # 7. 创建 CodeExecutorAgent
            # =================================================
            code_executor_agent = CodeExecutorAgent(
                name="CodeExecutor",
                code_executor=docker_executor,

                # 只执行 Engineer 发来的代码
                sources=["Engineer"],
            )

            print("\n" + "=" * 60)
            print("③ 把 Engineer 的回复交给 CodeExecutorAgent")
            print("=" * 60)

            # =================================================
            # 8. 把真正 Engineer 的回复交给 CodeExecutorAgent
            # =================================================
            executor_response = await code_executor_agent.on_messages(
                [engineer_response.chat_message],
                CancellationToken(),
            )

            # =================================================
            # 9. 打印 Docker 的执行结果
            # =================================================
            print("\n" + "=" * 60)
            print("④ Docker 执行结果")
            print("=" * 60)
            print(executor_response.chat_message.content)

    finally:
        # =====================================================
        # 10. 关闭大模型客户端
        # =====================================================
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())