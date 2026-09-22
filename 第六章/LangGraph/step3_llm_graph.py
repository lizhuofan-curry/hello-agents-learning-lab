# 开始写第一个 LLM Node , 第一次把大模型接入 LangGraph
import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage,SystemMessage
from langgraph.graph import StateGraph,START,END

# 加载 .env
load_dotenv()

# 定义 State
class ChatState(TypedDict):
    question : str
    answer: str

# 创建大模型客户端
# 只要服务商提供的是 OpenAI 兼容接口，很多模型都可以通过它调用
llm = ChatOpenAI(
    model=os.getenv('LLM_MODEL_ID'),
    api_key = os.getenv('LLM_API_KEY'),
    base_url = os.getenv('LLM_BASE_URL'),
    temperature=0.7
)

# 定义 LLM 节点
def llm_node(state: ChatState):
    print('进入 llm_node')

    # message 为列表，说明模型调用的通常不是只有一句话
    message = [
        # 相当于 role = system
        SystemMessage(
            content="你是一名耐心的人工智能老师，请用通俗易懂的中文回答问题。"
        ),
        # 相当于 role = user
        HumanMessage(
            content=state["question"]   # 说明用户的问题来自 State
        )
    ]
    # llm.invoke 意思是调用一次大模型
    # app.invoke 意思是运行整张 LangGraph
    # 这里返回的 response一般是 AIMessage 里面有 content以及其他模型信息
    response = llm.invoke(message)
    print("response 类型：", type(response))
    print("完整 response：", response)
    # 这样返回才更新了 State
    return {'answer':response.content}

# 创建图
workflow = StateGraph(ChatState)

# 添加节点
workflow.add_node('llm',llm_node)

# 添加边
workflow.add_edge(START,'llm')
workflow.add_edge('llm',END)

# 编译
app = workflow.compile()

# 执行
result = app.invoke({
    'question': '用最简单的话解释什么是 Transformer',
    'answer':''
})

# 输出
print('\n模型回答:')
print(result['answer'])