import asyncio
import os

from dotenv import load_dotenv

from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter


load_dotenv()


async def main():

    # =========================
    # 1. 创建模型
    # =========================
    model = OpenAIChatModel(
        model_name=os.getenv("LLM_MODEL_ID"),
        api_key=os.getenv("LLM_API_KEY"),
        stream=False,
        client_args={
            "base_url": os.getenv("LLM_BASE_URL"),
            "timeout": float(os.getenv("LLM_TIMEOUT", "60")),
        },
    )


    # =========================
    # 2. 创建刘备 Agent
    # =========================
    liubei = ReActAgent(
        name="刘备",

        sys_prompt="""
你是刘备。
你正在参加一场三国主题的讨论。
请用现代中文简洁回答问题。
""",

        model=model,

        formatter=OpenAIChatFormatter(),
    )


    # =========================
    # 3. 创建诸葛亮 Agent
    # =========================
    zhuge = ReActAgent(
        name="诸葛亮",

        sys_prompt="""
你是诸葛亮。
你善于分析其他人的发言。
请用现代中文简洁回答问题。
""",

        model=model,

        formatter=OpenAIChatFormatter(),
    )


    # =========================
    # 4. 用户先问刘备
    # =========================
    question_to_liubei = Msg(
        name="主持人",
        role="user",
        content="刘备，你认为这次行动应该进攻还是防守？"
    )


    # =========================
    # 5. 刘备回答
    # =========================
    # 这里直接将 liubei_response 的回答传给 zhugei了
    # 原理是这里面本身自带了 name = 'liubei',role = 'assistant',content = 刘备的回答
    # 这也就是 A2A的基础
    liubei_response = await liubei(question_to_liubei)

    print("\n========== 刘备的回答 ==========")
    print(liubei_response.content)


    # =========================
    # 6. 让诸葛亮听见刘备的回答
    # =========================
    await zhuge.observe(liubei_response)


    # =========================
    # 7. 主持人再问诸葛亮
    # =========================
    question_to_zhuge = Msg(
        name="主持人",
        role="user",
        content="诸葛亮，刚才刘备是什么意见？你怎么看？"
    )


    # =========================
    # 8. 诸葛亮回答
    # =========================
    zhuge_response = await zhuge(question_to_zhuge)

    print("\n========== 诸葛亮的回答 ==========")
    print(zhuge_response.content)


if __name__ == "__main__":
    asyncio.run(main())
