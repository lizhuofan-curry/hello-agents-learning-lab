import os
import asyncio
from datetime import datetime

from typing import TypedDict, Annotated

from dotenv import load_dotenv

from pydantic import BaseModel, Field

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)

from langchain_core.tools import tool

from langchain_openai import ChatOpenAI

from langgraph.graph import (
    StateGraph,
    START,
    END
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
# 2. Reviewer 的结构化输出
# =========================================================
class ReviewDecision(BaseModel):

    passed: bool = Field(
        description="当前回答是否已经足够完整、准确并回答了用户问题"
    )

    feedback: str = Field(
        description="如果回答不合格，说明应该如何改进；如果合格可以简单说明原因"
    )


# =========================================================
# 3. Agent State
# =========================================================
class AgentState(TypedDict):

    # 聊天历史
    messages: Annotated[
        list,
        add_messages
    ]

    # Reviewer 是否认为答案合格
    review_passed: bool

    # Reviewer 给出的修改意见
    review_feedback: str

    # 已经反思了几次
    reflection_count: int


# =========================================================
# 4. 初始化普通 LLM
# =========================================================
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0.7
)


# =========================================================
# 5. Reviewer LLM
# =========================================================
review_llm = llm.with_structured_output(
    ReviewDecision
)


# =========================================================
# 6. Tavily
# =========================================================
tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


# =========================================================
# 7. Tool 1：网页搜索
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
# 8. Tool 2：计算器
# =========================================================
@tool
def calculator(
    expression: str
) -> str:
    """
    计算数学表达式。

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
# 9. Tool 3：当前时间
# =========================================================
@tool
def get_current_time() -> str:
    """
    获取当前本地日期和时间。
    """

    print(
        "\n========== get_current_time 工具正在执行 =========="
    )

    now = datetime.now()

    return now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# =========================================================
# 10. 工具箱
# =========================================================
tools = [
    web_search,
    calculator,
    get_current_time
]


# =========================================================
# 11. 把工具绑定给 LLM
# =========================================================
llm_with_tools = llm.bind_tools(
    tools
)


# =========================================================
# 12. Agent Node
# =========================================================
def agent_node(
    state: AgentState
):

    print(
        "\n========== 进入 agent 节点 =========="
    )


    # -----------------------------------------------------
    # 基础系统提示词
    # -----------------------------------------------------
    system_prompt = """
你是一个智能助手。

你拥有以下工具：

1. web_search
   用于搜索天气、新闻、最新论文、
   当前价格、最新事件等外部信息。

2. calculator
   用于数学计算。

3. get_current_time
   用于查询当前日期和时间。


工具使用原则：

- 如果能直接回答，不要调用工具。
- 实时信息使用 web_search。
- 数学计算使用 calculator。
- 当前时间使用 get_current_time。
- 工具执行后，根据工具结果回答用户。
"""


    # -----------------------------------------------------
    # 如果 Reviewer 给过反馈
    # 把反馈加入 Prompt
    # -----------------------------------------------------
    if state["review_feedback"]:

        system_prompt += f"""

上一次回答经过 Reviewer 检查后，
发现下面的问题：

{state["review_feedback"]}

请根据这个反馈改进回答。

如果已有工具结果足够，
可以直接重新组织答案。

如果确实缺少必要信息，
可以继续调用合适的工具。
"""


    system_message = SystemMessage(
        content=system_prompt
    )


    # -----------------------------------------------------
    # 调用带工具的 LLM
    # -----------------------------------------------------
    response = llm_with_tools.invoke(

        [
            system_message
        ]
        + state["messages"]
    )


    print(
        "\n模型文本内容：",
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
# 13. ToolNode
# =========================================================
tool_node = ToolNode(
    tools
)


# =========================================================
# 14. Review Node
# =========================================================
def review_node(
    state: AgentState
):

    print(
        "\n========== 进入 review 节点 =========="
    )


    # -----------------------------------------------------
    # 获取最近一条 AI 最终回答
    # -----------------------------------------------------
    latest_answer = ""

    for msg in reversed(
        state["messages"]
    ):

        if (
            isinstance(msg, AIMessage)
            and
            not msg.tool_calls
            and
            msg.content
        ):

            latest_answer = (
                msg.content
            )

            break


    # -----------------------------------------------------
    # 找最新用户问题
    # -----------------------------------------------------
    latest_user_question = ""

    for msg in reversed(
        state["messages"]
    ):

        if isinstance(
            msg,
            HumanMessage
        ):

            latest_user_question = (
                msg.content
            )

            break


    # -----------------------------------------------------
    # Reviewer Prompt
    # -----------------------------------------------------
    review_prompt = f"""
你是一名严格但合理的 Reviewer。

请检查下面的回答是否已经足够好。


用户问题：

{latest_user_question}


Agent 回答：

{latest_answer}


检查标准：

1. 是否真正回答了用户的问题
2. 是否存在明显遗漏
3. 如果涉及工具结果，是否合理利用
4. 是否存在明显逻辑问题
5. 是否需要补充关键信息


注意：

不要因为回答不够长就判定失败。

如果答案已经足够正确、完整、有帮助，
应该判定通过。

如果确实存在重要缺陷，
再判定不通过并指出具体修改意见。
"""


    # -----------------------------------------------------
    # Structured Output
    # -----------------------------------------------------
    decision = review_llm.invoke(
        [
            SystemMessage(
                content=review_prompt
            )
        ]
    )


    print(
        "\nReviewer 结果：",
        decision
    )


    # -----------------------------------------------------
    # 更新反思次数
    # -----------------------------------------------------
    new_count = (
        state["reflection_count"]
        + 1
    )


    return {

        "review_passed":
            decision.passed,

        "review_feedback":
            decision.feedback,

        "reflection_count":
            new_count
    }


# =========================================================
# 15. agent 之后的 Router
# =========================================================
def route_after_agent(
    state: AgentState
):

    # -----------------------------------------------------
    # 找最新 AIMessage
    # -----------------------------------------------------
    latest_ai = None

    for msg in reversed(
        state["messages"]
    ):

        if isinstance(
            msg,
            AIMessage
        ):

            latest_ai = msg

            break


    # -----------------------------------------------------
    # 如果模型请求调用工具
    # -----------------------------------------------------
    if (
        latest_ai
        and
        latest_ai.tool_calls
    ):

        return "tools"


    # -----------------------------------------------------
    # 如果没有调用工具
    # 说明生成了一个回答
    # 去 review
    # -----------------------------------------------------
    return "review"


# =========================================================
# 16. review 之后的 Router
# =========================================================
def route_after_review(
    state: AgentState
):

    print(
        "\n========== Reflection Router =========="
    )


    # -----------------------------------------------------
    # 情况 1：
    # Reviewer 通过
    # -----------------------------------------------------
    if state["review_passed"]:

        print(
            "Reviewer：回答合格，结束。"
        )

        return "end"


    # -----------------------------------------------------
    # 情况 2：
    # 已经反思两次
    # 防止无限循环
    # -----------------------------------------------------
    if (
        state["reflection_count"]
        >= 2
    ):

        print(
            "达到最大反思次数，结束。"
        )

        return "end"


    # -----------------------------------------------------
    # 情况 3：
    # 不合格，并且还有机会
    # -----------------------------------------------------
    print(
        "Reviewer：回答需要改进，重新进入 Agent。"
    )

    return "retry"


# =========================================================
# 17. 创建 Graph
# =========================================================
def create_agent():

    workflow = StateGraph(
        AgentState
    )


    # -----------------------------------------------------
    # Nodes
    # -----------------------------------------------------
    workflow.add_node(
        "agent",
        agent_node
    )

    workflow.add_node(
        "tools",
        tool_node
    )

    workflow.add_node(
        "review",
        review_node
    )


    # -----------------------------------------------------
    # START → agent
    # -----------------------------------------------------
    workflow.add_edge(
        START,
        "agent"
    )


    # -----------------------------------------------------
    # agent：
    # 有工具调用 → tools
    # 没工具调用 → review
    # -----------------------------------------------------
    workflow.add_conditional_edges(

        "agent",

        route_after_agent,

        {
            "tools":
                "tools",

            "review":
                "review"
        }
    )


    # -----------------------------------------------------
    # tools → agent
    # -----------------------------------------------------
    workflow.add_edge(
        "tools",
        "agent"
    )


    # -----------------------------------------------------
    # review：
    #
    # 合格 → END
    # 不合格 → agent
    # -----------------------------------------------------
    workflow.add_conditional_edges(

        "review",

        route_after_review,

        {
            "end":
                END,

            "retry":
                "agent"
        }
    )


    # -----------------------------------------------------
    # Memory
    # -----------------------------------------------------
    memory = InMemorySaver()


    app = workflow.compile(
        checkpointer=memory
    )


    return app


# =========================================================
# 18. main
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
        "\n🤖 Step 11 Reflection Agent 启动！"
    )

    print(
        "输入 quit 退出。\n"
    )


    config = {

        "configurable": {

            "thread_id":
                "reflection-session-1"
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


        # -------------------------------------------------
        # 每次新用户问题
        # 重置本轮 Reflection 状态
        # -------------------------------------------------
        initial_state = {

            "messages": [

                HumanMessage(
                    content=user_input
                )
            ],

            "review_passed":
                False,

            "review_feedback":
                "",

            "reflection_count":
                0
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


                    # =====================================
                    # Agent
                    # =====================================
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


                            # 如果是最终文本回答
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
                                    "\n💬 Agent 当前回答："
                                )

                                print(
                                    message.content
                                )


                    # =====================================
                    # Tools
                    # =====================================
                    elif (
                        node_name
                        == "tools"
                    ):

                        print(
                            "\n🔧 工具执行完成"
                        )


                    # =====================================
                    # Review
                    # =====================================
                    elif (
                        node_name
                        == "review"
                    ):

                        print(
                            "\n🧐 Reviewer 检查完成"
                        )

                        print(
                            "通过：",
                            node_output[
                                "review_passed"
                            ]
                        )

                        print(
                            "反馈：",
                            node_output[
                                "review_feedback"
                            ]
                        )

                        print(
                            "当前反思次数：",
                            node_output[
                                "reflection_count"
                            ]
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
# 19. 程序入口
# =========================================================
if __name__ == "__main__":

    asyncio.run(
        main()
    )