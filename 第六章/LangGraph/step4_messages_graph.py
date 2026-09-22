import os
# Annotated 是 Python 类型系统提供的东西
# 可以理解成：在一个普通类型旁边，再贴一张‘说明标签’
# 例如 Annotated[int,'年龄'] 主体类型还是 int,只是额外加“年龄”这个信息
from typing import TypedDict,Annotated

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages

load_dotenv()

# 定义 State
class ChatState(TypedDict):
    # 先拆成 list + add_messages
    # list 意思是 ChatState 里面有一个 messages ,messages 是一个列表
    # 可以读成 这是一个 list ,另外告诉 LangGraph，这个字段更新的时候使用 add_messages 规则
    # add_messages 是 State 更新规则，这类规则通常叫做 Reducer
    # add_messages 可以理解成 告诉 LangGraph 更新时不要简单覆盖，而是按照 add_messages 的规则合并信息
    # 旧消息 + 新消息 = 完整消息历史
    # 所以下面的意思是 messages是一个列表，当节点返回新信息的时候，不直接覆盖原列表，而是用 add_messages将消息合并
    messages : Annotated[list,add_messages]

# 创建模型
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0.7
)

# LLM 节点
def chat_node(state: ChatState):
    print('进入 chat_node')

    print('\n当前 State 中的 messages:')

    for message in state['messages']:
        print(type(message),message.content)
    response = llm.invoke(state['messages'])

    # 这里不会把 [messages]直接替换成 [response],因为前面定义过
    return {'messages': [response]}

# 创建图
workflow = StateGraph(ChatState)

# 添加节点
workflow.add_node("chat", chat_node)

# 添加边
workflow.add_edge(START, "chat")
workflow.add_edge("chat", END)

# 编译
app = workflow.compile()

# 执行
result = app.invoke({
    'messages':[
    HumanMessage(
        content='请用一句话解释什么是注意力机制'
    )
]
})

# 查看最终 State
print('\n最终 messages:')

for message in result['messages']:
    print(type(message))
    print(message.content)
    print()