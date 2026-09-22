import asyncio
import os

from dotenv import load_dotenv

from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIMultiAgentFormatter
from agentscope.pipeline import fanout_pipeline


load_dotenv()


async def main():

    # ==========================================
    # 1. 创建模型
    # ==========================================
    model = OpenAIChatModel(
        model_name=os.getenv("LLM_MODEL_ID"),
        api_key=os.getenv("LLM_API_KEY"),
        stream=False,
        client_args={
            "base_url": os.getenv("LLM_BASE_URL"),
            "timeout": float(os.getenv("LLM_TIMEOUT", "60")),
        },
    )


    # ==========================================
    # 2. 创建刘备
    # ==========================================
    liubei = ReActAgent(
        name="刘备",

        sys_prompt="""
你是刘备。
现在需要独立判断军事方案。
请明确选择“进攻”或“防守”，并用50字以内说明原因。
""",

        model=model,
        formatter=OpenAIMultiAgentFormatter(),
    )


    # ==========================================
    # 3. 创建诸葛亮
    # ==========================================
    zhuge = ReActAgent(
        name="诸葛亮",

        sys_prompt="""
你是诸葛亮。
现在需要独立判断军事方案。
请明确选择“进攻”或“防守”，并用50字以内说明原因。
""",

        model=model,
        formatter=OpenAIMultiAgentFormatter(),
    )


    # ==========================================
    # 4. 创建同一个问题
    # ==========================================
    question = Msg(
        name="主持人",
        role="user",
        content="我军兵力不足，敌军远道而来。请选择进攻还是防守。",
    )


    # ==========================================
    # 5. 把同一个问题发送给两个 Agent
    # ==========================================
    responses = await fanout_pipeline(
        agents=[liubei, zhuge],
        msg=question,
        enable_gather=False,
    )


    # ==========================================
    # 6. 查看所有 Agent 的回答
    # ==========================================
    print("\n========== Fanout 返回结果 ==========")

    for response in responses:
        print(f"\n{response.name}：")
        print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
