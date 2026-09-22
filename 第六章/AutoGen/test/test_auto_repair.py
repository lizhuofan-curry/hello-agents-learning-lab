import asyncio
from pathlib import Path

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.conditions import FunctionalTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor



def reviewer_passed(messages):
    """
        只有 Reviewer 最终明确回复 REVIEW_PASS 时才结束。
        ThoughtEvent 等内部事件即使出现 REVIEW_PASS，也不算通过。
    """
    for message in messages:
        if (
            isinstance(message, TextMessage)
            and message.source == "Reviewer"
            and message.content.strip() == "REVIEW_PASS"
        ):
            return True

    return False


async def main():

    # =========================================================
    # 1. 创建大模型客户端
    # =========================================================
    model_client = create_openai_model_client()

    # =========================================================
    # 2. 创建 Engineer
    # =========================================================
    engineer = AssistantAgent(
        name="Engineer",
        model_client=model_client,
        system_message="""
你是一名 Python 软件工程师。

你的任务是根据用户要求编写完整、可运行的 Python 代码。

规则：

1. 第一次收到用户任务时：
   必须输出完整 Python 代码。
   代码必须放在且只放在一个 ```python ... ``` Markdown 代码块中。
   第一次必须只打印纯数字计算结果，例如：
   5050

2. 如果后续 Reviewer 返回 REVIEW_FAIL：
   必须仔细阅读 Reviewer 提出的修改要求。
   根据 Reviewer 的要求修改上一版代码。

3. 修改时必须重新输出完整代码，
   不能只输出修改的几行。

4. 每一次代码都必须放在一个完整的
   ```python ... ```
   Markdown 代码块中。

5. 不要拒绝 Reviewer 提出的合理修改要求。
""",
    )

    # =========================================================
    # 3. 创建 Reviewer
    # =========================================================
    reviewer = AssistantAgent(
        name="Reviewer",
        model_client=model_client,
        system_message="""
你是一名代码审查员。

你需要检查 Engineer 最新代码以及 CodeExecutor 最新运行结果。

审查规则：

如果 CodeExecutor 当前输出只有：

5050

那么必须回复：

REVIEW_FAIL
程序计算正确，但是输出格式不符合最终要求。
请把输出修改为：
结果是: 5050

如果 CodeExecutor 当前输出已经包含：

结果是: 5050

那么回复：

REVIEW_PASS

不要编写代码。
""",
    )

    # =========================================================
    # 4. 创建 Docker 工作目录
    # =========================================================
    work_dir = Path("../agent_workspace")
    work_dir.mkdir(exist_ok=True)

    try:

        # =====================================================
        # 5. 创建 Docker 代码执行器
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
            # 7. REVIEW_PASS 出现时终止
            # =================================================
            # 不要用过于宽松的字符串匹配来控制关键工作流
            # 之前那个TextMentionTermination("REVIEW_PASS") 相当于：谁说 REVIEW_PASS都算
            termination = FunctionalTermination(reviewer_passed)

            # =================================================
            # 8. 创建团队
            # =================================================
            team = RoundRobinGroupChat(
                participants=[
                    engineer,
                    code_executor,
                    reviewer,
                ],

                termination_condition=termination,

                # 最多允许两轮完整的：
                # Engineer -> Executor -> Reviewer
                max_turns=6,
            )

            # =================================================
            # 9. 用户任务
            # =================================================
            task = """
请编写一个 Python 程序：

计算 1 到 100 所有整数之和，并打印结果。

要求：
1. 使用 Python
2. 程序必须完整可运行
3. 不需要解释代码
"""

            # =================================================
            # 10. 启动团队
            # =================================================
            result = await Console(
                team.run_stream(task=task)
            )

            # =================================================
            # 11. 输出停止原因
            # =================================================
            print("\n" + "=" * 60)
            print("团队停止原因：")
            print(result.stop_reason)

    finally:
        # =====================================================
        # 12. 关闭模型客户端
        # =====================================================
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())