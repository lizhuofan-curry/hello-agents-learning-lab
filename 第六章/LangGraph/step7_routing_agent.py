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

# 加载环境变量
load_dotenv()

# 定义 State
class SearchState(TypedDict):
    # 保存聊天历史
    messages : Annotated[list,add_messages]
    # 对用户问题的理解
    user_query:str
    # 搜索关键词
    search_query : str
    search_results: str
    # 是否需要搜索
    need_search : bool
    # 最终答案
    final_answer : str
    # 当前步骤
    step : str

# 初始化 LLM
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0.7
)

# 初始化 Tavily
tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

# Node 1 : 理解用户问题 + 判断是否需要搜索
def understand_query_node(state:SearchState):
    print("\n========== 进入 understand 节点 ==========")

    # 获取最近几条聊天记录
    recent_messages = state['messages'][-6:]

    # 转成人类容易读的文本
    conversation_text = ''
    for msg in recent_messages:
        if isinstance(msg,HumanMessage):
            role = '用户'
        elif isinstance(msg,AIMessage):
            role = '助手'
        else :
            continue
        conversation_text += f'{role} : {msg.content}\n'

    print('\n最近对话：')
    print(conversation_text)

    # 找最新用户对话
    latest_user_message = ''

    for msg in reversed(state['messages']):
        if isinstance(msg,HumanMessage):
            latest_user_message = msg.content
            break

    # 让 LLM 做三件事 ：
    # 1. 理解问题
    # 2. 判断是否需要搜索
    # 3. 生成搜索词
    understand_prompt =  f"""
    下面是最近的对话历史：
    
    {conversation_text}
    
    
    请结合上下文，
    理解用户最新的问题。
    
    
    你需要完成三个任务：
    
    
    1. 理解用户真正想了解什么
    
    
    2. 判断这个问题是否需要联网搜索
    
    
    以下情况通常需要搜索：
    
    - 天气
    - 新闻
    - 最新论文
    - 实时信息
    - 当前价格
    - 最新政策
    - 最近发生的事情
    - 需要外部资料验证的问题
    
    
    以下情况通常不需要搜索：
    
    - 普通聊天
    - 用户告诉你自己的信息
    - 基础知识解释
    - 数学计算
    - 一般推理
    - 根据当前聊天历史即可回答的问题
    
    
    3. 如果需要搜索，
    生成适合搜索引擎使用的关键词。
    
    
    请严格使用下面格式：
    
    
    理解：[用户需求总结]
    
    是否搜索：[是/否]
    
    搜索词：[搜索关键词]
    
    
    如果不需要搜索：
    
    搜索词：[无需搜索]
    """

    # 调用 LLM
    response = llm.invoke([SystemMessage(content=understand_prompt)])
    print('\nLLM 分析结果：')
    print(response.content)

    # 提取是否需要搜索
    need_search = False

    if '是否搜索：是' in response.content:
        need_search = True
    elif '是否搜索:是' in response.content:
        need_search = True

    # 默认搜索词
    search_query = latest_user_message

    # 如果确实需要搜索，再提取搜索关键词
    if need_search:
        if "搜索词：" in response.content:
            search_query = (response.content.split("搜索词：")[1].strip())

    else:
        search_query=""
    print('\n是否需要搜索：',need_search)
    print('最终搜索关键词：',search_query)

    # 更新 State
    return {

        "user_query":response.content,
        "search_query":search_query,
        "need_search":need_search,
        "step":"understood"
    }

# Router : understand 之后决定去哪
def route_after_understand(state:SearchState):
    print("\n========== Router 正在选择路线 ==========")
    if state['need_search']:
        print('判断结果：需要搜索')
        return 'search'

    print('判断结果：不需要搜索')
    return 'direct'

# Node 2 : Tacily 搜索
def tavily_search_node(state:SearchState):
    print("\n========== 进入 search 节点 ==========")
    search_query = (state["search_query"])
    print('准备搜索：',search_query)
    try:
        # 调用 Tavily
        response = tavily_client.search(
            query=search_query,
            search_depth='basic',
            include_answer=True,
            include_raw_content=False,
            max_results=5
        )
        search_results = ''

        # Tavily 综合答案
        if response.get('answer'):
            search_results += ('综合答案：\n' + response['answer']+ '\n\n')

        # 具体搜索结果
        if response.get('results'):
            search_results += ('相关信息：\n')
            for i,result in enumerate(response['results'][:3],1):
                title = result.get('title',"")
                content = result.get('content',"")
                url = result.get('url',"")
                search_results +=f"""
                {i}·{title}
                {content}
                来源
                {url}
                """
        if not search_results:
            search_results = "没有找到相关信息"
        print('\n搜索完成')

        return {'search_results':search_results,'step':'searched'}

    # 搜索异常
    except Exception as e:
        error_msg = {f'搜索时发生错误：{str(e)}'}
        print( "\n❌",error_msg)
        return {
            "search_results":f"搜索失败：{error_msg}",
            "step":"search_failed"
        }

# Node 3 : 基于搜索结果回答
def generate_answer_node(state:SearchState):
    print("\n========== 进入 answer 节点 ==========")
    # 搜索失败
    if (state["step"]=="search_failed"):
        prompt = f"""
        搜索失败。
        
        请结合已有知识回答用户问题。
        
        
        用户需求：
        
        {state["user_query"]}
        
        
        请明确说明：
        
        回答没有使用实时搜索结果。
        """
    # 搜索成功
    else:
        prompt = f"""
        请根据搜索结果回答用户的问题。


        用户需求：

        {state["user_query"]}


        搜索结果：

        {state["search_results"]}


        要求：

        1. 综合搜索结果
        2. 不要编造搜索结果中没有的信息
        3. 结构清晰
        4. 如果来源存在冲突，要明确说明
        """
    response = llm.invoke([SystemMessage(content=prompt)])

    return {

        "final_answer":
            response.content,

        "step":
            "completed",

        "messages": [
            AIMessage(
                content=response.content
            )
        ]
    }

# Node 4 : 不搜索，直接回答
def direct_answer_node(state:SearchState):
    print("\n========== 进入 direct_answer 节点 ==========")

    # 获取最近的聊天历史
    recent_messages = state['messages'][-8:]

    # 直接让 LLM 基于对话历史问答
    response = llm.invoke(recent_messages)
    return {

        "final_answer":
            response.content,

        "step":
            "completed",

        "messages": [
            response
        ]
    }

# 创建 Graph
def create_search_assistant():
    workflow = StateGraph(SearchState)
    # 添加四个节点
    workflow.add_node('understand',understand_query_node)
    workflow.add_node('search',tavily_search_node)
    workflow.add_node('answer',generate_answer_node)
    workflow.add_node('direct_answer',direct_answer_node)

    # START -> understand
    workflow.add_edge(START,'understand')

    # 条件边
    workflow.add_conditional_edges(
        'understand',
        route_after_understand,
        {
            'search':'search',
            'direct' : 'direct_answer'
        }
    )

    # 搜索路线
    workflow.add_edge('search','answer')
    workflow.add_edge('answer',END)

    # 直接回答路线
    workflow.add_edge('direct_answer',END)

    # Checkpointer
    memory = InMemorySaver()

    app = workflow.compile(checkpointer=memory)

    return app

# main
async def main():
    if not os.getenv('TAVILY_API_KEY'):
        print("❌ 没有检测到 TAVILY_API_KEY" )
        return
    app  = create_search_assistant()

    print("\n🤖 Step 7 智能路由 Agent 启动！")
    print("输入 quit 退出。\n")

    # 整个程序一直重复使用同一个 thread
    config = {
        'configurable':{
            'thread_id':'search_session-1'
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
            ],

            "user_query": "",

            "search_query": "",

            "search_results": "",

            "need_search": False,

            "final_answer": "",

            "step": "start"
        }

        try:
            print("\n"+ "=" * 60)
            async for output in app.astream(initial_state,config=config):
                for (node_name,node_output) in output.items():
                    if (node_name == 'understand'):
                        print("\n🧠 理解完成")
                    elif (node_name == 'search'):
                        print("\n🔍 搜索完成")
                    elif (node_name == 'answer'):
                        print( "\n💡 搜索回答：")
                        print(node_output['final_answer'])
                    elif (node_name == 'direct_answer'):
                        print("\n💬 直接回答：")
                        print(node_output['final_answer'])
            print("\n" + "=" * 60)
        except Exception as e:
            print("\n❌ 程序运行失败：",e)

# 程序入口
if __name__ == '__main__':
    asyncio.run(main())