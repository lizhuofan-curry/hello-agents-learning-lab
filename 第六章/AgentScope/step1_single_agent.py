# 属于Python的异步编程库
import asyncio
# 主要是用来读取环境变量
import os

# 把当前 .env文件中的内容加载到当前Python程序的环境变量里
# load.dotenv()是加载 ， os.getenv()是读取
from dotenv import load_dotenv

from agentscope.agent import ReActAgent         # 意思是创建一个Agent
from agentscope.message import Msg              # Agent之间传递的消息
from agentscope.model import OpenAIChatModel    # 调用大语言模型
from agentscope.formatter import OpenAIChatFormatter    # 把AgentScope消息整理成模型 API 能接受的格式

# 自动读取当前项目或父目录中的 .env
load_dotenv()

# async 表示异步函数，也叫做协程函数
# 因为在调用 LLM 时，大部分时间 Python 实际上不是在计算，而是在发送请求->等待服务器->等待模型生成 -> 等待结果返回
async def main():
    # 1.创建模型
    # 这里只是创建了一个大语言模型调用器
    model = OpenAIChatModel(
        model_name = os.getenv("LLM_MODEL_ID"), # 告诉调用哪一个模型
        api_key = os.getenv("LLM_API_KEY"),
        stream= False,  # 关闭流式输出
        client_args={
            # 创建底层 OpenAI-compatible 客户端时的额外配置
            # 虽然调用的是 OpenAIChatModel 但实际上请求的是 ModelScope
            "base_url":os.getenv("LLM_BASE_URL"),
            "timeout": float(os.getenv("LLM_TIMEOUT", "60")),
        },
    )

    # 2.真正创建 Agent
    agent = ReActAgent(
        name = '诸葛亮',
        sys_prompt='''
        你是诸葛亮。
        你是一名善于分析问题的军师。
        请用现代中文清晰、简洁地回答问题。
        ''',
        model = model,
        # 可以理解成消息翻译器，Formatter 负责把消息整理成类似模型接口要求的形式
        formatter=OpenAIChatFormatter(),
    )

    # 3，主持人偷偷告诉诸葛亮身份
    secret_msg = Msg(
        name = '游戏主持人',
        role = 'user',
        content= '你的真实身份是预言家。这个信息请记住'
    )
    # 让诸葛亮“听见”这个信息,这里的 observe的意思是听，还不需要回答
    # 严格的说 observe(msg) 意思是 消息进入 Agent 上下文 / memory
    await agent.observe(secret_msg)

    print("主持人的秘密消息已经发送给诸葛亮。")
    print("注意：此时诸葛亮没有回答。\n")

    # 5.用户再问一个问题
    question = Msg(
        name = 'user',
        role = 'user',
        content= '请告诉我，你在这局游戏中的身份是什么?'
    )

    # 6.这一次才真正让 Agent 回答
    # agent(msg) -> 接收消息 -> 进入 reply() -> 调用模型 -> 生成回答 -> 返回 Msg
    # AgentScope 的 AgentBase 本身就把 reply，observe，print 抽象成 Agent 的三个核心行为，其中 observe 明确是不返回响应的
    # 这也就是 AgentScope 把 收到消息和轮到我发言故意拆开
    # 这就是后面 MsgHub 能控制多 Agent 对话秩序的基础
    response = await agent(question)    # 这说明诸葛亮回答当前问题时，能利用之前 observe()收到的信息

    print("\n========== 最终返回 ==========")
    print(response)

if __name__ == '__main__':
    asyncio.run(main())
