import asyncio  # 负责异步函数
import os       # 读取 .env 中的环境变量

from dotenv import load_dotenv  # 把 .env 文件加载进来
# 这是 Structured Output 的核心
# choice: Literal["进攻", "防守"] 可以理解成 choice 这个变量，只允许取这两个值
# 所以 Literal 的作用就是 限制字段只能取规定好的几个值
from typing import Literal
# 这个BaseModel 来自 pydantic , pydantic 是专门来做 数据结构定义+数据验证的
# 普通的python类，可以随便塞数据，但是Pydantic类会检查 类型对不对，范围合不合法
from pydantic import BaseModel, Field

from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIMultiAgentFormatter
from agentscope.pipeline import fanout_pipeline


load_dotenv()

# 可以把 MilitaryDecision 想成一个 JSON 模板，这就是 Structured Output 的结构化
class MilitaryDecision(BaseModel):
    # 这可以拆成两部分
    # 1.choice: Literal["进攻", "防守"] 负责类型限制
    # 2.Field(description="最终选择，只能是进攻或防守") 负责告诉模型这个字段是什么意思，会帮助模型理解
    choice: Literal["进攻", "防守"] = Field(
        description="最终选择，只能是进攻或防守"
    )
    # 说明原因必须是字符串
    reason: str = Field(
        description="做出这个选择的主要原因"
    )
    # 给一个数并要求输出范围
    confidence: int = Field(
        description="对这个决定的信心程度，1到10",
        ge=1,
        le=10,
    )

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
        # 用 MilitaryDecision 来约束
        # 不允许 Agent 只返回自由文本，还要按照 MilitaryDecision 的格式生成结构化结果
        structured_model = MilitaryDecision,
        # 表示先调用刘备再调用诸葛亮，不是并发
        enable_gather=False,
    )


    # ==========================================
    # 6. 查看所有 Agent 的回答
    # ==========================================
    print("\n========== Structured Output ==========")

    for response in responses:
        print(f"\n{response.name}：")

        print("完整 Msg：")
        print(response)

        print("metadata：")
        # response 本身还是 Msg
        # 但是 Structured Output 的结果会被放进 response.metadata
        # 所以里面的 content 是给人看，但是 metadata是给程序用
        print(response.metadata)

        print("选择：")
        print(response.metadata.get("choice"))

        print("理由：")
        print(response.metadata.get("reason"))

        print("信心：")
        print(response.metadata.get("confidence"))

if __name__ == "__main__":
    asyncio.run(main())
