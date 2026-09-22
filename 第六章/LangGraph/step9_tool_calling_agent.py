import os

import asyncio

from typing import TypedDict, Annotated

from dotenv import load_dotenv
from langchain_core.messages import (HumanMessage,AIMessage,SystemMessage)
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph,START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode,tools_condition

from tavily import TavilyClient

load_dotenv()

class AgentState(TypedDict):
    messages : Annotated[list,add_messages]

llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0.7
)

tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

# 定义工具,以前 def web_search() 只是一个普通的python函数
# 现在加上 @tool 之后就变成了一个 LLM 可以认识的 Tool
# LLM知道工具的名字 web_search ,工具作用：搜索互联网实时信息 ，需要的参数 query：str
@tool
def web_search(query:str)-> str:
    '''
    搜索互联网中的最新或实时信息
    当用户询问天气，新闻，最新论文
     最新价格，最新事件等需要外部信息的问题时使用

     Args: query : 搜索关键词
    '''
    print("\n========== web_search 工具正在执行 ==========")
    print('搜索关键词：',query)

    try:
        response = tavily_client.search(
            query=query,
            search_depth='basic',
            include_answer=True,
            include_raw_content=False,
            max_results=5
        )
        search_results = ''

        # Tavily 综合回答
        if response.get('answer'):
            search_results += ('综合答案：\n' + response['answer'] + '\n\n')

        # Tavily 具体搜索结果
        if response.get('results'):
            search_results += ('相关搜索结果：\n\n')
            for i,result in enumerate(response['results'][:3],1):
                title = result.get('title',"")
                content = result.get('content',"")
                url = result.get('url',"")
                search_results += f"""
                {i}. {title}
                
                {content}
                
                来源：
                {url}
                
                """
        if not search_results:
            search_results = "没有搜索到相关信息。"

        return search_results
    except Exception as e:
         return (f"搜索工具调用失败：{str(e)}")

# 工具列表
tools = [web_search]

# 把工具绑定给 LLM
# 普通的 llm 只会 输入文字 -> 输出文字
# 在绑定工具之后 就可以输入文字 LLM 回答文字或者请求调用工具
# LangChain 官方描述说 ： 用 bind_tools() 把工具提供给模型后，模型可根据输入自行选择是否调用某个工具
llm_with_tools = llm.bind_tools(tools)

# Agent Node
def agent_node(state:AgentState):
    print( "\n========== 进入 agent 节点 ==========")
    # 系统提示词
    system_message = SystemMessage(
        content="""
    你是一个智能助手。

    你拥有 web_search 工具。

    使用规则：

    1. 如果问题涉及天气、新闻、最新信息、
       当前价格、最新论文、近期事件等，
       请调用 web_search 工具。

    2. 如果只是基础知识解释、普通聊天、
       数学推理、或者根据当前对话历史
       就能回答的问题，不要调用搜索工具。

    3. 如果调用了工具，
       请根据工具返回的信息回答用户。

    4. 不要为了调用工具而调用工具。
    """
    )

    # 带 Tool Calling 能力的 LLM
    response = llm_with_tools.invoke([system_message]+state['messages'])

    # 看看模型有没有要求调用工具
    print('\n模型返回类型：',type(response))
    print('模型文本内容',response.content)
    print('Tool Calls:',response.tool_calls)

    # 把 AIMessage 加到 messages
    return {'messages': [response]}

# 创建 ToolNode
# LLM 并不会真正执行工具,它实际上只会返回一个 AIMessage
# 官方也明确区分了这两步： 模型先返回 tool call 请求，随后需要执行工具，再把结果送回模型
tool_node = ToolNode(tools)     # 它才是真正执行工具的，可以理解成 LangGraph 自带的工具执行器

# 创建 Graph
def creat_agent():
    workflow = StateGraph(AgentState)

    # 添加 Agent Node
    workflow.add_node('agent',agent_node)
    # 添加 Tool Node
    workflow.add_node('tools',tool_node)

    workflow.add_edge(START,'agent')
    # agent 执行完之后 tools_condition 会检查 AIMessage 有没有 tool_calls
    # step 8 我们自己写的路由，现在路由不用我们自己写了，tool_condition 会帮我们检查最新 AIMessage 有没有 tool_calls
    # 如果有就 -> tools 如果没有就 ->END
    workflow.add_conditional_edges('agent',tools_condition)

    # 工具执行完之后再回到 agent
    # 为什么不是 tools -> END 因为工具只负责查资料，不负责组织最终回答
    workflow.add_edge('tools','agent')

    memory = InMemorySaver()

    app = workflow.compile(checkpointer=memory)

    return app

async def main():
    if not os.getenv('TAVILY_API_KEY'):
        print("❌ 没有检测到 TAVILY_API_KEY")
        return

    app = creat_agent()
    print("\n🤖 Step 9 Tool Calling Agent 启动！")

    # 固定 thread
    config = {
        'configurable':{
            'thread_id':'tool-session-1'
        }
    }

    while True:
        user_input = input("🤔 您想了解什么：").strip()

        if user_input.lower() in ["quit","q","exit","退出"]:
            print("\n再见 👋")
            break

        if not user_input:
            continue

        initial_state = {

            "messages": [

                HumanMessage(
                    content=user_input
                )
            ]
        }

        try:
            print("\n"+ "=" * 60)
            async for output in app.astream(initial_state,config=config):
                for (node_name,node_output) in output.items():
                    # Agent Node
                    if node_name == 'agent':
                        if ('messages' in node_output and node_output['messages']):
                            message = node_output['messages'][-1]

                        # 如果没有 Tool Call 说明这已经是最终回答
                        if (isinstance(message,AIMessage) and not message.tool_calls and message.content):
                            print("\n💬 Agent 回答：")
                            print(message.content)

                    # Tool Node
                    elif node_name == 'tools':
                        print( "\n🔧 工具执行完成")
            print("\n" + "=" * 60)

        except Exception as e:
            print("\n❌ 程序运行失败：",e)

if __name__ == '__main__':
    asyncio.run(main())




