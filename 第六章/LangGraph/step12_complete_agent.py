import os
import asyncio
from datetime import datetime
from typing import TypedDict, Annotated

from dotenv import load_dotenv

from pydantic import BaseModel, Field

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage
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

from langgraph.prebuilt import ToolNode

from tavily import TavilyClient


# =========================================================
# 0. 环境变量
# =========================================================
load_dotenv()


# =========================================================
# 1. Structured Output
# =========================================================
class ReviewDecision(BaseModel):

    passed: bool = Field(
        description="当前回答是否已经足够正确、完整、可靠"
    )

    feedback: str = Field(
        description="如果不通过，给出具体修改意见；如果通过，可说明原因"
    )


# =========================================================
# 2. State
# =========================================================
class AgentState(TypedDict):

    # 完整消息历史
    messages: Annotated[
        list,
        add_messages
    ]

    # Reviewer 是否通过
    review_passed: bool

    # Reviewer 的反馈
    review_feedback: str

    # 当前已经反思几次
    reflection_count: int


# =========================================================
# 3. 初始化 LLM
# =========================================================
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0.7
)


# Reviewer 使用结构化输出
review_llm = llm.with_structured_output(
    ReviewDecision
)


# =========================================================
# 4. Tavily
# =========================================================
tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


# =========================================================
# 5. Tools
# =========================================================

# ---------------------------------------------------------
# Tool 1：网页搜索
# ---------------------------------------------------------
@tool
def web_search(query: str) -> str:
    """
    搜索互联网中的最新或实时信息。

    适合：
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
        "\n========== web_search =========="
    )

    print(
        "query:",
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

        result_text = ""

        if response.get("answer"):

            result_text += (
                "综合答案：\n"
                + response["answer"]
                + "\n\n"
            )

        if response.get("results"):

            result_text += (
                "搜索结果：\n\n"
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

                result_text += f"""
{i}. {title}

{content}

来源：
{url}

"""

        if not result_text:

            result_text = (
                "没有搜索到相关信息。"
            )

        return result_text

    except Exception as e:

        return (
            f"搜索失败：{str(e)}"
        )


# ---------------------------------------------------------
# Tool 2：计算器
# ---------------------------------------------------------
@tool
def calculator(
    expression: str
) -> str:
    """
    计算数学表达式。

    Args:
        expression: 数学表达式，例如 123 * 456
    """

    print(
        "\n========== calculator =========="
    )

    print(
        "expression:",
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


# ---------------------------------------------------------
# Tool 3：当前时间
# ---------------------------------------------------------
@tool
def get_current_time() -> str:
    """
    获取当前本地日期和时间。
    """

    print(
        "\n========== get_current_time =========="
    )

    now = datetime.now()

    return now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# =========================================================
# 6. 工具箱
# =========================================================
tools = [
    web_search,
    calculator,
    get_current_time
]


tool_node = ToolNode(
    tools
)


llm_with_tools = llm.bind_tools(
    tools
)


# =========================================================
# 7. Agent Node
# =========================================================
def agent_node(
    state: AgentState
):

    print(
        "\n========== Agent Node =========="
    )


    system_prompt = """
你是一个具备工具调用能力的智能助手。

你拥有：

1. web_search
   查询实时或外部信息。

2. calculator
   数学计算。

3. get_current_time
   获取当前日期和时间。


工作原则：

- 能直接回答时，不要调用工具。
- 实时信息优先使用 web_search。
- 时间相关问题使用 get_current_time。
- 数学计算使用 calculator。
- 可以连续调用多个工具。
- 工具结果返回后，再生成最终回答。
- 不要编造工具没有提供的关键事实。
"""


    # -----------------------------------------------------
    # 如果上一轮 Reviewer 不满意
    # 把反馈加入 Agent Prompt
    # -----------------------------------------------------
    if state["review_feedback"]:

        system_prompt += f"""

上一版回答经过 Reviewer 检查后，
收到以下反馈：

{state["review_feedback"]}

请认真修正这些问题。

如果已有工具证据足够，
优先利用已有信息重新组织答案。

只有确实缺少必要信息时，
再调用新的工具。
"""


    response = llm_with_tools.invoke(

        [
            SystemMessage(
                content=system_prompt
            )
        ]
        + state["messages"]
    )


    print(
        "content:",
        response.content
    )

    print(
        "tool_calls:",
        response.tool_calls
    )


    return {

        "messages": [
            response
        ]
    }


# =========================================================
# 8. Review Node
# =========================================================
def review_node(
    state: AgentState
):

    print(
        "\n========== Review Node =========="
    )


    # -----------------------------------------------------
    # 1. 获取最新用户问题
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
    # 2. 获取最新最终回答
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
    # 3. 收集 Tool Evidence
    # -----------------------------------------------------
    tool_evidence = ""

    for msg in state["messages"]:

        if isinstance(
            msg,
            ToolMessage
        ):

            tool_evidence += f"""
-------------------------
Tool Evidence
-------------------------

{msg.content}

"""


    # -----------------------------------------------------
    # 4. Reviewer Prompt
    # -----------------------------------------------------
    review_prompt = f"""
你是一名严格但合理的 Reviewer。

请检查 Agent 的回答质量。


=========================
用户问题
=========================

{latest_user_question}


=========================
Agent 回答
=========================

{latest_answer}


=========================
工具证据
=========================

{tool_evidence if tool_evidence else "本轮没有使用工具"}


=========================
检查标准
=========================

1. 是否真正回答用户问题

2. 核心事实是否准确

3. 如果存在工具证据：
   - 回答是否与工具结果一致
   - 不要把工具明确返回的信息误判为幻觉

4. 如果多个工具结果存在冲突：
   应检查 Agent 是否合理处理了冲突

5. 实时问题应注意数据时间

6. 不要因为回答不够长就判定失败

7. 轻微措辞问题不应阻止通过

8. 只有存在会明显影响用户理解或决策的重要问题，
   才判定为不通过


如果回答已经足够正确、完整、可靠：

passed = True

否则：

passed = False

并在 feedback 中说明具体修改方法。
"""


    decision = review_llm.invoke(

        [
            SystemMessage(
                content=review_prompt
            )
        ]
    )


    print(
        "passed:",
        decision.passed
    )

    print(
        "feedback:",
        decision.feedback
    )


    return {

        "review_passed":
            decision.passed,

        "review_feedback":
            decision.feedback,

        "reflection_count":
            state["reflection_count"]
            + 1
    }


# =========================================================
# 9. Router：Agent 后面去哪
# =========================================================
def route_after_agent(
    state: AgentState
):

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
    # 有工具请求
    # -----------------------------------------------------
    if (
        latest_ai
        and
        latest_ai.tool_calls
    ):

        print(
            "\nRouter：Agent → Tools"
        )

        return "tools"


    # -----------------------------------------------------
    # 没有工具请求
    # -----------------------------------------------------
    print(
        "\nRouter：Agent → Review"
    )

    return "review"


# =========================================================
# 10. Router：Review 后面去哪
# =========================================================
def route_after_review(
    state: AgentState
):

    print(
        "\n========== Review Router =========="
    )


    # -----------------------------------------------------
    # 通过
    # -----------------------------------------------------
    if state["review_passed"]:

        print(
            "Review 通过 → END"
        )

        return "end"


    # -----------------------------------------------------
    # 最大反思次数
    # -----------------------------------------------------
    if (
        state["reflection_count"]
        >= 2
    ):

        print(
            "达到最大 Reflection 次数 → END"
        )

        return "end"


    # -----------------------------------------------------
    # 不通过，再修改
    # -----------------------------------------------------
    print(
        "Review 不通过 → Agent"
    )

    return "retry"


# =========================================================
# 11. 创建 Graph
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
    # START
    # -----------------------------------------------------
    workflow.add_edge(
        START,
        "agent"
    )


    # -----------------------------------------------------
    # Agent Router
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
    # Tools 回 Agent
    # -----------------------------------------------------
    workflow.add_edge(
        "tools",
        "agent"
    )


    # -----------------------------------------------------
    # Review Router
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


    return workflow.compile(
        checkpointer=memory
    )


# =========================================================
# 12. Main
# =========================================================
async def main():

    if not os.getenv(
        "TAVILY_API_KEY"
    ):

        print(
            "❌ 未检测到 TAVILY_API_KEY"
        )

        return


    app = create_agent()


    print(
        "\n🤖 Step 12 Complete LangGraph Agent 启动！"
    )

    print(
        "输入 quit 退出。\n"
    )


    # -----------------------------------------------------
    # 固定 thread_id
    # 保持同一会话 Memory
    # -----------------------------------------------------
    config = {

        "configurable": {

            "thread_id":
                "complete-agent-session-1"
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
        # 每个新问题：
        #
        # messages 会通过 add_messages + Memory 合并
        #
        # Reflection 状态重新初始化
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
                + "=" * 70
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

                            msg = (
                                node_output[
                                    "messages"
                                ][-1]
                            )


                            if (
                                isinstance(
                                    msg,
                                    AIMessage
                                )
                                and
                                not msg.tool_calls
                                and
                                msg.content
                            ):

                                print(
                                    "\n💬 当前回答："
                                )

                                print(
                                    msg.content
                                )


                    # =====================================
                    # Tools
                    # =====================================
                    elif node_name == "tools":

                        print(
                            "\n🔧 Tool 执行完成"
                        )


                    # =====================================
                    # Review
                    # =====================================
                    elif node_name == "review":

                        print(
                            "\n🧐 Review 完成"
                        )

                        print(
                            "passed:",
                            node_output[
                                "review_passed"
                            ]
                        )

                        print(
                            "feedback:",
                            node_output[
                                "review_feedback"
                            ]
                        )

                        print(
                            "reflection_count:",
                            node_output[
                                "reflection_count"
                            ]
                        )


            print(
                "\n"
                + "=" * 70
                + "\n"
            )


        except Exception as e:

            print(
                "\n❌ 程序运行失败：",
                e
            )


# =========================================================
# 13. 程序入口
# =========================================================
if __name__ == "__main__":

    asyncio.run(
        main()
    )