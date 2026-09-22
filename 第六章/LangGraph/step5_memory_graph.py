import os
from typing import TypedDict,Annotated

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
# 在电脑内存 RAM 里创建一个“小存档管理员”
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

# 定义 State
class ChatState(TypedDict):
    messages : Annotated[list,add_messages]

# 创建模型
llm = ChatOpenAI(
model=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0.7
)

# 定义 LLM 节点
def chat_node(state: ChatState):
    print('\n进入 chat_node')

    print('当前 State 中共有',len(state['messages']),'条信息')

    for message in state['messages']:
        print(type(message).__name__,':',message.content)

    response = llm.invoke(state['messages'])
    return {'messages': [response]}

# 创建工作流
workflow = StateGraph(ChatState)

workflow.add_node('chat',chat_node)

workflow.add_edge(START,'chat')
workflow.add_edge('chat',END)

# 创建 Checkpointer
# add_messages 解决同一个 State内，新旧 message 怎么合并
# InMemorySaver 解决：一次 invoke 结束后，这个 State怎么留给下一次的 invoke
# 也就是 add_messages 负责怎么加信息，InMemorySaver负责怎么跨调用保存状态
# 两者结合起来才能形成真正的多轮聊天
# 还有一个重要限制 InMemorySaver 是存在程序内存里的，退出后之前的记忆就没了
memory = InMemorySaver()

# 编译,此处多了 checkpointer = memory
# 翻译成人话就是 ： 编译这张图的时候，给它安装一个存档系统
app = workflow.compile(checkpointer=memory)

# 定义同一个对话线程
config = {'configurable':{
    # 意思就是这一轮对话属于编号 conversation-1 的线程 ，可以想象成游戏编号或者微信聊天窗口A
    # 而 thread_id 意思就是以后不可能只有一个用户，多个用户同时在和 Agent聊的时候，LangGraph必须知道这条消息到底属于哪一段聊天
    'thread_id':'conversation-1'
}}
config2 = {'configurable':{
    # 意思就是这一轮对话属于编号 conversation-1 的线程 ，可以想象成游戏编号或者微信聊天窗口A
    # 而 thread_id 意思就是以后不可能只有一个用户，多个用户同时在和 Agent聊的时候，LangGraph必须知道这条消息到底属于哪一段聊天
    'thread_id':'conversation-2'
}}

# 第一轮对话
print('\n========== 第一轮 ==========')
result1 = app.invoke({
    'messages':[
        HumanMessage(content='我叫小明，请记住我的名字')
    ]
},config=config
)
print('\nAI:')
print(result1['messages'][-1].content)

# 第二轮对话
print('\n========= 第二轮 =========')
result2 = app.invoke(
    {
        'messages':[
            HumanMessage(content='我叫什么名字')
        ]
    },
    # 第二轮对话的用户仍是第一轮的，所以就找到之前的State，继续往里面添加消息
    # 所谓多轮对话的短期记忆，核心思想就是把历史保存下来，重新塞给模型
    config=config2
)
print('\nAI:')
print(result2['messages'][-1].content)

# 查看最终完整消息历史
print('\n============= 完整消息历史 ===========')
for message in result2['messages']:
    print(type(message).__name__,':',message.content)