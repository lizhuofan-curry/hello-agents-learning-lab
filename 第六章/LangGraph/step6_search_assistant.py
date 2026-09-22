import os
import asyncio

from typing import TypedDict,Annotated

from dotenv import load_dotenv

from langchain_core.messages import HumanMessage,AIMessage,SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

from tavily import TavilyClient

# 加载 .env
load_dotenv()

# 定义整个 LangGraph 的 State
class SearchState(TypedDict):
    # 保存聊天信息
    # add_messages 负责把新消息和旧消息合并
    messages : Annotated[list,add_messages]

    user_query : str # 对用户需求的理解

    search_query : str  # 真正交给 Tavily 的搜索关键词

    search_results : str    # Tavily 返回的搜索结果

    final_answer : str  # 最终生成的答案

    step : str  # 当前执行到哪个阶段

# 初始化 LLM
llm = ChatOpenAI(
    model = os.getenv('LLM_MODEL_ID'),
    api_key = os.getenv('LLM_API_KEY'),
    base_url=os.getenv('LLM_BASE_URL'),
    temperature= 0.7
)

# 初始化 Tavily 搜索客户端
tavily_client = TavilyClient(
    api_key=os.getenv('TAVILY_API_KEY')
)

# Node 1 : 理解用户问题
def understand_query_node(state: SearchState):
    print("\n========== 进入 understand 节点 ==========")

    # 从 messages 中倒着找最近一条 HumanMessage
    # user_message = ''

    # 从聊天历史末尾往前找最新的 HumanMessage
    #for msg in reversed(state['messages']):
        # message 中不会只有用户信息，所以不能直接 State['message'][-1].content
        #if isinstance(msg,HumanMessage):
        #   user_message = msg.content
        #    break
    recent_messages = state["messages"][-6:]
    conversation_text = ''
    for msg in recent_messages:
        if isinstance(msg,HumanMessage):
            role = '用户'
        elif isinstance(msg,AIMessage):
            role = '助手'
        else:
            continue
        conversation_text += f"{role}: {msg.content}\n"

    # 让 LLM 帮忙把 自然语言变成搜索任务
    understand_prompt = f"""
    下面是最近的对话历史：

    {conversation_text}

    请结合上下文，理解用户最新的问题。

    请完成两个任务：

    1. 简洁总结用户真正想了解什么
    2. 生成适合搜索引擎使用的搜索关键词

    请严格使用下面格式：

    理解：[用户需求总结]

    搜索词：[搜索关键词]
    """

    # 调用 LLM
    response = llm.invoke(
        [
            SystemMessage(content=understand_prompt),
        ]
    )

    print('\nLLM对问题的理解：')
    print(response.content)

    # 默认情况下 ： 搜索词 = 用户原始问题
    latest_user_message = ""

    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            latest_user_message = msg.content
            break
    search_query = latest_user_message

    # 尝试从 LLM 输出中提取 ： 搜索词 XXXX
    if '搜索词：' in response.content:
        search_query = response.content.split('搜索词：')[1].strip()
    elif '搜索关键词：' in response.content:
        search_query = response.content.split('搜索关键词：')[1].strip()

    print('\n最终搜索关键词：',search_query)

    # 更新 State
    return {
        'user_query': response.content,
        'search_query': search_query,
        'step' : 'understood',
        'messages':[AIMessage(content=f'我理解您的需求：{response.content}')]
    }

# Node 2 : 使用 Tavily 搜索
def tavily_search_node(state: SearchState):
    print('\n========= 进入 search 节点 ===========')

    # 从 State 中读取搜索关键词
    search_query = state['search_query']

    print('准备搜索:',search_query)

    try:
        # 调用 Tavily API
        response = tavily_client.search(
            # 这里体现了 understand Node 的价值
            query=search_query,
            search_depth= 'basic',
            include_answer=True,
            include_raw_content=False,
            max_results=5   # 最多拿五条
        )

        # 用字符串保存整理后的搜索结果
        search_results = ''
        '''
        Tavily 返回的结果长这样：
        {
            "answer": "...",
            "results": [
                        {
                        "title": "...",
                        "content": "...",
                        "url": "..."
                        },
                        ...
                        ]
        }
        '''
        # 如果 Tavily 给出了综合答案
        if response.get('answer'):
            search_results += ('综合答案 ：\n' + response['answer'] + '\n\n')

        # 获取具体搜索结果
        if response.get('results'):
            search_results += '相关信息: \n'

            # 这里只取前 3 个结果
            for i,result in enumerate(
                response['results'][:3],
                1
            ):
                title = result.get('title','')
                content = result.get('content','')
                url = result.get('url','')
                search_results +=f'''{i}·{title}
                {content}
                来源：
                {url}
                '''

        # 如果什么都没搜到
        if not search_results:
            search_results = ('抱歉，没有找到相关信息')
        print('\n搜索完成')

        # 更新 State
        return {
            'search_results': search_results,
            'step':'searched',
            'messages':[AIMessage(content=( "✅ 搜索完成！""正在为您整理答案..."))]
        }
    # 如果 Tavily 搜索失败
    except Exception as e:
        error_msg = (f'搜索时发生错误：{str(e)}')
        print("\n❌", error_msg)
        return {
            'search_results': (f'搜索失败：{error_msg}'),
            'step':'search_failed',
            'messages':[AIMessage(content=('❌ 搜索遇到问题，''我将基于已有知识回答.'))]
        }

# Node 3: 生成最终答案
def generate_answer_node(state:SearchState):
    print("\n========== 进入 answer 节点 ==========")

    # 情况 1：
    # Tavily 搜索失败
    if state['step'] == 'search_failed':
        fallback_prompt = f'''
        搜索 API 当前不可用。

        请基于你已有的知识回答下面的问题：

        用户问题：

        {state["user_query"]}
        请提供一个清楚、有帮助的回答。

        同时说明：
        这是基于模型已有知识生成的回答。
        '''
        response = llm.invoke([SystemMessage(content=fallback_prompt)])

        return {
            'final_answer':response.content,
            'step':'completed',
            'messages':[AIMessage(content=response.content)]
        }
    # 情况 2：
    # 搜索成功
    answer_prompt = f'''
    请根据下面的搜索结果回答用户的问题。

    用户问题：
    
    {state["user_query"]}
    
    
    搜索结果：
    
    {state["search_results"]}
    
    
    回答要求：
    
    1. 综合搜索结果进行回答
    2. 回答准确、有用
    3. 如果是技术问题，可以给出具体解决方案
    4. 尽量保留重要信息来源
    5. 结构清晰，容易理解
    6. 如果搜索结果不够完整，请明确说明
    '''
    response = llm.invoke([SystemMessage(content=answer_prompt)])

    # 更新最终 State
    return {
        'final_answer': response.content,
        'step':'completed',
        'messages':[AIMessage(content=response.content)]
    }

# 创建完整的 LangGraph
def create_search_assistant():
    # 创建图
    workflow = StateGraph(SearchState)

    # 添加三个 Node
    workflow.add_node('understand',understand_query_node)
    workflow.add_node('search',tavily_search_node)
    workflow.add_node('answer',generate_answer_node)

    # 添加 Edge
    workflow.add_edge(START,'understand')
    workflow.add_edge('understand','search')
    workflow.add_edge('search','answer')
    workflow.add_edge('answer',END)

    # 创建 Checkpointer
    memory = InMemorySaver()

    # 编译
    app = workflow.compile(checkpointer=memory)

    return app

# 主函数
async def main():

    # 检查 Tavily API Key
    if not os.getenv("TAVILY_API_KEY") :
        print("❌ 没有检测到 TAVILY_API_KEY")
        print('请先在 .env 中配置')

        return

    # 创建 LangGraph 应用
    app = create_search_assistant()

    print("\n🔍 LangGraph 智能搜索助手启动！")
    print('输入 quit 可以退出。\n')

    # 用于生成不同的 thread_id
    session_count = 0

    config = {
        "configurable": {
            "thread_id": "search-session-1"
        }
    }

    # 不断接受用户问题
    while True:
        user_input = input( "🤔 您想了解什么：").strip()

        # 退出
        if user_input.lower() in ['quit','q','exit','退出']:
            print("\n再见 👋")
            break
        if not user_input:
            continue

        # 新建一次搜索会话
        session_count+=1

        # # thread_id
        # config = {
        #     'configurable':{
        #         'thread_id':config,
        #     }
        # }

        # 创建初始 State
        initial_state = {
            'messages': [
                HumanMessage(content=user_input)
            ],
            "user_query": "",

            "search_query": "",

            "search_results": "",

            "final_answer": "",

            "step": "start"
        }

        try:
            print("\n"+ "=" * 60)

            # 流式执行整个 LangGraph
            # 这样会一个 Node 一个 Node 地产出结果
            async for output in app.astream(
                initial_state,
                config = config
            ):
                # output 中可能包含不同 Node 的结果
                for (node_name,node_output) in output.items():
                    # 如果这个 Node 更新了 message
                    if ('messages' in node_output and node_output['messages']):
                        latest_message = node_output['messages'][-1]

                        # 只输出 AImessage
                        if isinstance(latest_message,AIMessage):
                            if (node_name == 'understand'):
                                print("\n🧠 理解阶段：")
                                print(latest_message.content)
                            elif (node_name == 'search'):
                                print( "\n🔍 搜索阶段：")
                                print( latest_message.content)
                            elif (node_name == 'answer'):
                                print("\n💡 最终回答：")
                                print(latest_message.content)

            print("\n"+ "=" * 60+ "\n")

        except Exception as e:
            print("\n❌ 程序运行失败：",e)

# 程序入口
if __name__ == '__main__':
    asyncio.run(main())


