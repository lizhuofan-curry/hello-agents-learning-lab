import os
import asyncio

from typing import TypedDict, Annotated

from dotenv import load_dotenv

# pydantic 主要是定义数据结构和检查数据类型
from pydantic import BaseModel, Field

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)

from langchain_openai import ChatOpenAI

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

from tavily import TavilyClient


# =========================================================
# 1. 加载环境变量
# =========================================================
load_dotenv()


# =========================================================
# 2. Structured Output Schema
# =========================================================
# 可以把它理解成 Java 里的一个数据类，或者 C++的结构体
# 这个类是一个 Pydantic 数据模型
class RouterDecision(BaseModel):
    # langChain 会把 Schema 信息提供给模型，让模型理解这个字段到底应该填什么
    # 所以 字段名 + 数据类型 + description 共同约束 LLM
    understanding: str = Field(
        description="结合聊天上下文，对用户最新需求的简洁理解"
    )

    need_search: bool = Field(
        description="如果需要实时或外部信息则为 True，否则为 False"
    )

    search_query: str = Field(
        description="如果需要搜索，给出适合搜索引擎的关键词；否则返回空字符串"
    )


# =========================================================
# 3. LangGraph State
# =========================================================
class SearchState(TypedDict):

    messages: Annotated[
        list,
        add_messages
    ]

    user_query: str

    search_query: str

    search_results: str

    need_search: bool

    final_answer: str

    step: str


# =========================================================
# 4. 普通 LLM
# =========================================================
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0.7
)


# =========================================================
# 5. 创建 Structured Output LLM
# =========================================================
# 可以理解成 普通 llm 套上一个输出模具 变成了 router_llm
router_llm = llm.with_structured_output(
    RouterDecision
)


# =========================================================
# 6. Tavily
# =========================================================
tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


# =========================================================
# 7. Node 1：
# 理解问题 + 判断是否搜索
# =========================================================
def understand_query_node(
    state: SearchState
):

    print(
        "\n========== 进入 understand 节点 =========="
    )


    # -----------------------------------------------------
    # 获取最近的聊天历史
    # -----------------------------------------------------
    recent_messages = (
        state["messages"][-6:]
    )


    # -----------------------------------------------------
    # 转成人类可读形式
    # -----------------------------------------------------
    conversation_text = ""


    for msg in recent_messages:

        if isinstance(
            msg,
            HumanMessage
        ):

            role = "用户"


        elif isinstance(
            msg,
            AIMessage
        ):

            role = "助手"


        else:

            continue


        conversation_text += (
            f"{role}: {msg.content}\n"
        )


    print("\n最近对话：")
    print(conversation_text)


    # -----------------------------------------------------
    # 构造 Router Prompt
    # -----------------------------------------------------
    prompt = f"""
下面是最近的对话历史：

{conversation_text}


请结合聊天上下文，
分析用户最新的问题。


判断规则：


通常需要搜索：

- 天气
- 新闻
- 最新论文
- 当前价格
- 最新政策
- 实时信息
- 最近发生的事件
- 需要外部资料验证的问题


通常不需要搜索：

- 普通聊天
- 用户告诉你的个人信息
- 根据聊天历史即可回答的问题
- 基础知识解释
- 一般数学计算
- 一般逻辑推理


如果需要搜索：

need_search = True

并生成适合搜索引擎的 search_query。


如果不需要搜索：

need_search = False

search_query 返回空字符串。
"""


    # =====================================================
    # Structured Output 调用
    # =====================================================
    decision = router_llm.invoke(
        [
            SystemMessage(
                content=prompt
            )
        ]
    )


    # -----------------------------------------------------
    # 查看返回类型
    # -----------------------------------------------------
    print(
        "\nStructured Output 类型：",
        type(decision)
    )


    print(
        "\nStructured Output 内容："
    )

    print(decision)


    # -----------------------------------------------------
    # 不再 split()
    # 直接读取字段
    # -----------------------------------------------------
    print(
        "\n问题理解：",
        decision.understanding
    )

    print(
        "是否需要搜索：",
        decision.need_search
    )

    print(
        "搜索关键词：",
        decision.search_query
    )


    # =====================================================
    # 更新 State
    # =====================================================
    return {

        "user_query":
            decision.understanding,

        "search_query":
            decision.search_query,

        "need_search":
            decision.need_search,

        "step":
            "understood"
    }


# =========================================================
# 8. Router
# =========================================================
def route_after_understand(
    state: SearchState
):

    print(
        "\n========== Router 正在选择路线 =========="
    )


    if state["need_search"]:

        print(
            "判断结果：需要搜索"
        )

        return "search"


    print(
        "判断结果：不需要搜索"
    )

    return "direct"


# =========================================================
# 9. Search Node
# =========================================================
def tavily_search_node(
    state: SearchState
):

    print(
        "\n========== 进入 search 节点 =========="
    )


    search_query = (
        state["search_query"]
    )


    print(
        "准备搜索：",
        search_query
    )


    try:

        response = tavily_client.search(

            query=search_query,

            search_depth="basic",

            include_answer=True,

            include_raw_content=False,

            max_results=5
        )


        search_results = ""


        # Tavily 综合答案
        if response.get("answer"):

            search_results += (
                "综合答案：\n"
                + response["answer"]
                + "\n\n"
            )


        # 具体搜索结果
        if response.get("results"):

            search_results += (
                "相关信息：\n"
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
                "没有找到相关信息。"
            )


        print("\n搜索完成")


        return {

            "search_results":
                search_results,

            "step":
                "searched"
        }


    except Exception as e:

        error_msg = (
            f"搜索时发生错误：{str(e)}"
        )


        print(
            "\n❌",
            error_msg
        )


        return {

            "search_results":
                f"搜索失败：{error_msg}",

            "step":
                "search_failed"
        }


# =========================================================
# 10. Search Answer Node
# =========================================================
def generate_answer_node(
    state: SearchState
):

    print(
        "\n========== 进入 answer 节点 =========="
    )


    if (
        state["step"]
        == "search_failed"
    ):

        prompt = f"""
搜索失败。

请基于已有知识回答下面的问题：

{state["user_query"]}

请明确说明：
当前回答没有使用实时搜索结果。
"""


    else:

        prompt = f"""
请根据搜索结果回答用户的问题。


用户需求：

{state["user_query"]}


搜索结果：

{state["search_results"]}


要求：

1. 根据搜索资料回答
2. 不要编造搜索结果中没有的信息
3. 结构清晰
4. 如果多个来源冲突，请指出
"""


    response = llm.invoke(
        [
            SystemMessage(
                content=prompt
            )
        ]
    )


    return {

        "final_answer":
            response.content,

        "step":
            "completed",

        "messages": [
            response
        ]
    }


# =========================================================
# 11. Direct Answer Node
# =========================================================
def direct_answer_node(
    state: SearchState
):

    print(
        "\n========== 进入 direct_answer 节点 =========="
    )


    recent_messages = (
        state["messages"][-8:]
    )


    response = llm.invoke(
        recent_messages
    )


    return {

        "final_answer":
            response.content,

        "step":
            "completed",

        "messages": [
            response
        ]
    }


# =========================================================
# 12. 创建 Graph
# =========================================================
def create_search_assistant():


    workflow = StateGraph(
        SearchState
    )


    # -----------------------------------------------------
    # Nodes
    # -----------------------------------------------------
    workflow.add_node(
        "understand",
        understand_query_node
    )


    workflow.add_node(
        "search",
        tavily_search_node
    )


    workflow.add_node(
        "answer",
        generate_answer_node
    )


    workflow.add_node(
        "direct_answer",
        direct_answer_node
    )


    # -----------------------------------------------------
    # START
    # -----------------------------------------------------
    workflow.add_edge(
        START,
        "understand"
    )


    # -----------------------------------------------------
    # Conditional Edge
    # -----------------------------------------------------
    workflow.add_conditional_edges(

        "understand",

        route_after_understand,

        {
            "search":
                "search",

            "direct":
                "direct_answer"
        }
    )


    # -----------------------------------------------------
    # Search 路线
    # -----------------------------------------------------
    workflow.add_edge(
        "search",
        "answer"
    )


    workflow.add_edge(
        "answer",
        END
    )


    # -----------------------------------------------------
    # Direct 路线
    # -----------------------------------------------------
    workflow.add_edge(
        "direct_answer",
        END
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


    app = create_search_assistant()


    print(
        "\n🤖 Step 8 Structured Router Agent 启动！"
    )

    print(
        "输入 quit 退出。\n"
    )


    # -----------------------------------------------------
    # 固定 thread_id
    # -----------------------------------------------------
    config = {

        "configurable": {

            "thread_id":
                "structured-session-1"
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


                    if (
                        node_name
                        == "understand"
                    ):

                        print(
                            "\n🧠 结构化理解完成"
                        )


                    elif (
                        node_name
                        == "search"
                    ):

                        print(
                            "\n🔍 搜索完成"
                        )


                    elif (
                        node_name
                        == "answer"
                    ):

                        print(
                            "\n💡 搜索回答："
                        )

                        print(
                            node_output[
                                "final_answer"
                            ]
                        )


                    elif (
                        node_name
                        == "direct_answer"
                    ):

                        print(
                            "\n💬 直接回答："
                        )

                        print(
                            node_output[
                                "final_answer"
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
# 14. 程序入口
# =========================================================
if __name__ == "__main__":

    asyncio.run(
        main()
    )