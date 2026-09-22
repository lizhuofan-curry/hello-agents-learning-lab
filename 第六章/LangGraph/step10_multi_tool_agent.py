import os
import asyncio
from datetime import datetime

from typing import TypedDict, Annotated

from dotenv import load_dotenv

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)

from langchain_core.tools import tool

from langchain_openai import ChatOpenAI

from langgraph.graph import (
    StateGraph,
    START
)

from langgraph.graph.message import add_messages

from langgraph.checkpoint.memory import InMemorySaver

from langgraph.prebuilt import (
    ToolNode,
    tools_condition
)

from tavily import TavilyClient


# =========================================================
# 1. 加载环境变量
# =========================================================
load_dotenv()


# =========================================================
# 2. State
# =========================================================
class AgentState(TypedDict):

    messages: Annotated[
        list,
        add_messages
    ]


# =========================================================
# 3. 初始化 LLM
# =========================================================
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0.7
)


# =========================================================
# 4. 初始化 Tavily
# =========================================================
tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


# =========================================================
# 5. Tool 1：网页搜索
# =========================================================
@tool
def web_search(query: str) -> str:
    """
    搜索互联网中的最新或实时信息。

    适用于：
    - 天气
    - 新闻
    - 最新论文
    - 当前价格
    - 最新事件
    - 需要外部信息验证的问题

    Args:
        query: 搜索关键词
    """

    print(
        "\n========== web_search 工具正在执行 =========="
    )

    print(
        "搜索关键词：",
        query
    )


    try:

        response = tavily_client.search(

            query=query,

            search_depth="basic",

            include_answer=True,

            include_raw_content=False,

            max_results=5
        )


        search_results = ""


        if response.get("answer"):

            search_results += (
                "综合答案：\n"
                + response["answer"]
                + "\n\n"
            )


        if response.get("results"):

            search_results += (
                "相关搜索结果：\n\n"
            )


            for i, result in enumerate(
                response["results"][:3],
                1
            ):

                title = result.get(
                    "title",
                    ""
                )

                content = result.get(
                    "content",
                    ""
                )

                url = result.get(
                    "url",
                    ""
                )


                search_results += f"""
{i}. {title}

{content}

来源：
{url}

"""


        if not search_results:

            search_results = (
                "没有搜索到相关信息。"
            )


        return search_results


    except Exception as e:

        return (
            f"搜索工具调用失败：{str(e)}"
        )


# =========================================================
# 6. Tool 2：计算器
# =========================================================
@tool
def calculator(
    expression: str
) -> str:
    """
    计算数学表达式。

    适用于：
    - 加减乘除
    - 括号运算
    - 数值计算

    示例：
    123 * 456
    (10 + 5) * 3

    Args:
        expression: 要计算的数学表达式
    """

    print(
        "\n========== calculator 工具正在执行 =========="
    )

    print(
        "计算表达式：",
        expression
    )


    try:

        # -------------------------------------------------
        # 简单学习版写法
        # 这里只用于本地实验
        # -------------------------------------------------
        # 把
        # "123 * 456"
        # 这样的字符串计算成数字。
        result = eval(
            expression,
            {"__builtins__": {}},
            {}
        )


        return (
            f"{expression} = {result}"
        )


    except Exception as e:

        return (
            f"计算失败：{str(e)}"
        )


# =========================================================
# 7. Tool 3：获取当前时间
# =========================================================
@tool
def get_current_time() -> str:
    """
    获取当前本地时间。

    当用户询问：
    - 现在几点
    - 当前时间
    - 今天日期

    等时间相关问题时使用。
    """

    print(
        "\n========== get_current_time 工具正在执行 =========="
    )


    now = datetime.now()


    return now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# =========================================================
# 8. 工具箱
# =========================================================
tools = [

    web_search,

    calculator,

    get_current_time
]


# =========================================================
# 9. 把多个工具绑定给 LLM
# =========================================================
llm_with_tools = llm.bind_tools(
    tools
)


# =========================================================
# 10. Agent Node
# =========================================================
def agent_node(
    state: AgentState
):

    print(
        "\n========== 进入 agent 节点 =========="
    )


    system_message = SystemMessage(
        content="""
你是一个智能助手。

你拥有三个工具：

1. web_search
   用于查询天气、新闻、最新信息、
   最新论文、价格、近期事件等。

2. calculator
   用于数学计算。

3. get_current_time
   用于查询当前时间和日期。


工具使用原则：

- 如果能直接回答，不要调用工具。
- 如果需要实时互联网信息，使用 web_search。
- 如果是数学计算，优先使用 calculator。
- 如果询问当前时间，使用 get_current_time。
- 工具执行完成后，根据工具返回结果回答用户。
"""
    )


    response = llm_with_tools.invoke(

        [
            system_message
        ]
        + state["messages"]
    )


    print(
        "\n模型返回类型：",
        type(response)
    )


    print(
        "模型文本内容：",
        response.content
    )


    print(
        "Tool Calls：",
        response.tool_calls
    )


    return {

        "messages": [
            response
        ]
    }


# =========================================================
# 11. ToolNode
# =========================================================
tool_node = ToolNode(
    tools
)


# =========================================================
# 12. 创建 Graph
# =========================================================
def create_agent():

    workflow = StateGraph(
        AgentState
    )


    # Agent
    workflow.add_node(
        "agent",
        agent_node
    )


    # Tools
    workflow.add_node(
        "tools",
        tool_node
    )


    # START -> agent
    workflow.add_edge(
        START,
        "agent"
    )


    # agent -> tools / END
    workflow.add_conditional_edges(
        "agent",
        tools_condition
    )


    # tools -> agent
    workflow.add_edge(
        "tools",
        "agent"
    )


    # Memory
    memory = InMemorySaver()


    app = workflow.compile(
        checkpointer=memory
    )


    return app


# =========================================================
# 13. main
# =========================================================
async def main():

    if not os.getenv(
        "TAVILY_API_KEY"
    ):

        print(
            "❌ 没有检测到 TAVILY_API_KEY"
        )

        return


    app = create_agent()


    print(
        "\n🤖 Step 10 Multi-Tool Agent 启动！"
    )


    print(
        "输入 quit 退出。\n"
    )


    config = {

        "configurable": {

            "thread_id":
                "multi-tool-session-1"
        }
    }


    while True:

        user_input = input(
            "🤔 您想了解什么："
        ).strip()


        if user_input.lower() in [
            "quit",
            "q",
            "exit",
            "退出"
        ]:

            print(
                "\n再见 👋"
            )

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

            print(
                "\n"
                + "=" * 60
            )


            async for output in app.astream(

                initial_state,

                config=config

            ):


                for (
                    node_name,
                    node_output
                ) in output.items():


                    if node_name == "agent":

                        if (
                            node_output
                            and
                            "messages"
                            in node_output
                            and
                            node_output["messages"]
                        ):

                            message = (
                                node_output[
                                    "messages"
                                ][-1]
                            )


                            if (
                                isinstance(
                                    message,
                                    AIMessage
                                )
                                and
                                not message.tool_calls
                                and
                                message.content
                            ):

                                print(
                                    "\n💬 Agent 回答："
                                )

                                print(
                                    message.content
                                )


                    elif node_name == "tools":

                        print(
                            "\n🔧 工具执行完成"
                        )


            print(
                "\n"
                + "=" * 60
                + "\n"
            )


        except Exception as e:

            print(
                "\n❌ 程序运行失败：",
                e
            )


# =========================================================
# 14. 程序入口
# =========================================================
if __name__ == "__main__":

    asyncio.run(
        main()
    )