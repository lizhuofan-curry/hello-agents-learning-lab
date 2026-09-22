import asyncio
import os

from dotenv import load_dotenv

from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
# 之前单Agent用的是 OpenAIChatFormatter() 主要根据 role 区分
# 现在多 Agent 用的是 OpenAIMultiAgentFormatter() 主要根据 name 区分
from agentscope.formatter import OpenAIMultiAgentFormatter
# MsgHub 负责的是 多个Agent之间的信息流动和组织，所以归档在 pipeline,也就是多 Agent 编排相关功能里
# 官方 Pipeline模块同时包含 MsgHub,sequential_pipeline和 fanout_pipeline
from agentscope.pipeline import MsgHub


# 读取之前的 .env
load_dotenv()


async def main():

    # ==================================================
    # 1. 创建模型
    # ==================================================
    model = OpenAIChatModel(
        model_name=os.getenv("LLM_MODEL_ID"),
        api_key=os.getenv("LLM_API_KEY"),
        stream=False,
        client_args={
            "base_url": os.getenv("LLM_BASE_URL"),
            "timeout": float(os.getenv("LLM_TIMEOUT", "60")),
        },
    )


    # ==================================================
    # 2. 创建刘备 Agent
    # ==================================================
    liubei = ReActAgent(
        name="刘备",

        sys_prompt="""
你是刘备。
你正在与诸葛亮讨论一次军事行动。
请明确表达自己的意见，并简洁说明原因。
""",

        model=model,

        formatter=OpenAIMultiAgentFormatter(),
    )


    # ==================================================
    # 3. 创建诸葛亮 Agent
    # ==================================================
    zhuge = ReActAgent(
        name="诸葛亮",

        sys_prompt="""
你是诸葛亮。
你正在与刘备讨论一次军事行动。
请认真考虑刘备之前的发言，然后给出自己的分析。
""",

        model=model,

        formatter=OpenAIMultiAgentFormatter(),
    )


    # ==================================================
    # 4. 主持人发布讨论主题
    # ==================================================
    announcement = Msg(
        name="主持人",
        role="user",
        content="现在讨论：我军兵力不足，应该主动进攻还是暂时防守？",
    )


    # ==================================================
    # 5. 创建 MsgHub
    # ==================================================
    # 可以理解成打开一个临时聊天室，打开自动广播，离开自动关闭聊天室
    async with MsgHub(
        # 这个列表就是聊天室成员的名单
        [liubei, zhuge],
        # 表示一进入这个聊天室，就把主持人的公告发给所有参与者
        announcement=announcement,
        # 表示 Hub 中某个 Agent 产生回复后，MsgHub 自动把这条消息发送给其他Agent
        enable_auto_broadcast=True,
    ):

        # 刘备先发言
        liubei_response = await liubei()

        print("\n========== 刘备发言结束 ==========\n")

        # 诸葛亮再发言
        zhuge_response = await zhuge()

        print("\n========== 诸葛亮发言结束 ==========\n")


    # ==================================================
    # 6. 看看返回值
    # ==================================================
    print("刘备返回的 Msg：")
    print(liubei_response)

    print("\n诸葛亮返回的 Msg：")
    print(zhuge_response)


if __name__ == "__main__":
    asyncio.run(main())
