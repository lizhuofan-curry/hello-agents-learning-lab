import asyncio
from pathlib import Path

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor

from OpenAiClient import create_openai_model_client, create_engineer


async def main():

    # =========================================================
    # 1. 创建大模型客户端
    # =========================================================
    model_client = create_openai_model_client()

    # =========================================================
    # 2. 创建 Engineer
    # =========================================================
    engineer = create_engineer(model_client)

    # =========================================================
    # 3. 创建 Reviewer
    # =========================================================
    reviewer = AssistantAgent(
        name="Reviewer",
        model_client=model_client,
        system_message="""
你是一名代码审查员。

你的任务是同时检查：

1. Engineer 编写的 Python 代码是否满足用户要求
2. CodeExecutor 的实际运行结果是否正确
3. 是否存在明显逻辑错误
4. 是否成功执行

如果代码正确，并且实际运行结果也正确，
请回复：

REVIEW_PASS

如果存在问题，请回复：

REVIEW_FAIL

然后说明具体问题。

不要编写新的代码。
"""
    )

    # =========================================================
    # 4. 创建 Docker 工作目录
    # =========================================================
    work_dir = Path("../agent_workspace")
    work_dir.mkdir(exist_ok=True)

    try:

        # =====================================================
        # 5. 创建 Docker Executor
        # =====================================================
        async with DockerCommandLineCodeExecutor(
            image="python:3.12-slim",
            work_dir=work_dir,
            timeout=30,
        ) as docker_executor:

            # =================================================
            # 6. 创建 CodeExecutorAgent
            # =================================================
            code_executor = CodeExecutorAgent(
                name="CodeExecutor",
                code_executor=docker_executor,

                # 只执行 Engineer 发出的代码
                sources=["Engineer"],
            )

            # =================================================
            # 7. 设置终止条件
            # =================================================
            # 告诉团队，只要聊天中出现 REVIEW_PASS,任务就可以结束
            termination = TextMentionTermination("REVIEW_PASS")

            # =================================================
            # 8. 创建三人团队
            # =================================================
            team = RoundRobinGroupChat(
                participants=[
                    engineer,
                    code_executor,
                    reviewer,
                ],
                termination_condition=termination,

                # 当前实验最多运行 3 轮
                max_turns=3,
            )

            # =================================================
            # 9. 用户任务
            # =================================================
            task = """
请编写一个 Python 程序：

计算 1 到 100 所有整数的和，并打印最终结果。

要求：
1. 使用 Python
2. 给出完整可运行代码
3. 必须放在完整的 ```python ... ``` Markdown 代码块中
4. 不需要解释代码
"""

            # =================================================
            # 10. 启动团队
            # =================================================
            result = await Console(
                team.run_stream(task=task)
            )

            # =================================================
            # 11. 打印停止原因
            # =================================================
            print("\n" + "=" * 60)
            print("团队停止原因：")
            print(result.stop_reason)

    finally:

        # =====================================================
        # 12. 关闭大模型客户端
        # =====================================================
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())