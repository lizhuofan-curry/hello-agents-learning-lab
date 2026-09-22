"""
AutoGen 软件开发团队协作案例
"""
import re
from pathlib import Path
# 主要是为了读取环境变量
import os
# 是 python的异步编程库，因为后面的 async def 是一个异步函数，所以最后需要 asyncio.run启动它
import asyncio
# RoundRobinGroupChat : 规定大家轮流说话
from autogen_agentchat.teams import RoundRobinGroupChat
# extMentionTermination : 规定什么时候结束
from autogen_agentchat.conditions import FunctionalTermination
from autogen_agentchat.messages import TextMessage
# AssistantAgent ： AI智能体 ；UserProxyAgent： 用户代理
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent,CodeExecutorAgent
# Console 把聊天过程打印出来
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from autogen_core import CancellationToken
from dotenv import load_dotenv
from web_app_tester import test_streamlit_app
# 加载环境变量
load_dotenv()

# 现在是一轮一轮执行，更方便直接从 Engineer的回复保存
def save_code_from_engineer_message(message, filename="output.py"):
    """
    从 Engineer 的 TextMessage 中提取 Python 代码，
    做语法检查，然后保存到 output.py。
    """

    content = message.content

    match = re.search(
        r"```python\s*(.*?)```",
        content,
        re.DOTALL,
    )

    if not match:
        raise ValueError(
            "Engineer 回复中没有找到完整的 Python Markdown 代码块"
        )

    code = match.group(1).strip()

    # Python 语法检查
    compile(code, filename, "exec")

    # 保存文件
    Path(filename).write_text(
        code,
        encoding="utf-8",
    )

    print(f"💾 Engineer 代码已保存到 {filename}")
    print("✅ Python 语法检查通过")

    return code

def save_engineer_code(result, filename="output.py"):
    """
    从团队聊天结果中找到 Engineer 最后生成的 Python 代码，
    并保存到 output.py
    """

    # 从后往前找 Engineer 的消息
    for message in reversed(result.messages):

        if getattr(message, "source", None) != "Engineer":
            continue

        content = getattr(message, "content", "")

        # 找 ```python ... ``` 代码块
        match = re.search(
            r"```python\s*(.*?)```",
            content,
            re.DOTALL
        )

        if match:
            code = match.group(1).strip()

            # 先进行 Python 语法检查
            compile(code, filename, "exec")

            # 语法正确后保存
            Path(filename).write_text(
                code,
                encoding="utf-8"
            )

            print(f"💾 Engineer 代码已保存到 {filename}")
            print("✅ Python 语法检查通过")

            return code

    raise ValueError("没有找到 Engineer 输出的 Python 代码块")


def create_code_executor(docker_executor):
    '''
    创建代码执行智能体
    注意：
    CodeExecutorAgent 自己不真正执行代码
    真正执行代码的是传进来的 DockerCommandLineCodeExecutor
    Docker Executor 里面有明确的：启动 -> 使用 -> 关闭 的生命周期
    '''
    return CodeExecutorAgent(
        name = "CodeExecutor",
        code_executor= docker_executor,
        sources= ['Engineer'],
    )

def reviewer_passed(messages):
    """
    只有 CodeReviewer 最终明确回复 REVIEW_PASS，
    整个开发流程才允许结束。
    """

    for message in messages:

        if (
            isinstance(message, TextMessage)
            and message.source == "CodeReviewer"
            and message.content.strip() == "REVIEW_PASS"
        ):
            return True

    return False

# AutoGen 提供了标准化的 OpenAIChatCompletionClient，方便与任何兼容 OpenAI API 规范的模型服务

# 通过一个独立的函数来创建和配置模型客户端
# 并通过环境变量管理 API Key 和服务地址
# 这是一种良好的工程实践，增强了代码的灵活性和安全性

def create_openai_model_client():
    '''创建并配置 OpenAI 模型客户端'''
    return OpenAIChatCompletionClient(
        model=os.getenv("LLM_MODEL_ID"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        # 相当于告诉模型有哪些能力
        model_info={
            "vision": True,
            "function_calling": False,
            "json_output": False,
            "family": "unknown",
            "structured_output": False,
        },
    )


# 下面来定义智能体角色
# 在软件开发团队中，我们为每一个角色都创建一个独立的函数来封装其定义

# 产品经理（Product Manager）
'''
产品经理负责启动整个流程。它的系统信息不仅定义了职责，还规范了其输出的结构
并包含了引导对话转向下一环节（工程师）的明确指令
LLM + 产品经理 System Prompt = ProductManager Agent
'''
def create_product_manager(model_client):
    """创建产品经理智能体"""
    system_message = """你是一位经验丰富的产品经理，专门负责软件产品的需求分析和项目规划。
你的核心职责包括：
1. **需求分析**：深入理解用户需求，识别核心功能和边界条件
2. **技术规划**：基于需求制定清晰的技术实现路径
3. **风险评估**：识别潜在的技术风险和用户体验问题
4. **协调沟通**：与工程师和其他团队成员进行有效沟通

当接到开发任务时，请按以下结构进行分析：
1. 需求理解与分析
2. 功能模块划分
3. 技术选型建议
4. 实现优先级排序
5. 验收标准定义

请简洁明了地回应，并在分析完成后说"请工程师开始实现"。"""
    # 这个请工程师开始实现，这只是语言层面的交接提示
    # RoundRobinGroupChat 才是真正让 Engineer 下一个发言
    return AssistantAgent(
        name = "ProductManager",
        model_client = model_client,
        system_message = system_message,
        model_client_stream=True,
    )

# 工程师（Engineer）
# 工程师的系统消息聚焦于技术实现
# 它列举了工程师的技术专长，并规定了其在接收到任务后的具体行动步骤
# 同样也包含了引导流程转向代码审查员的指令
def create_engineer(model_client):
    """创建软件工程师智能体"""
    system_message = """
    你是一位资深的软件工程师，擅长 Python 开发和 Web 应用构建。

    你的职责是根据用户需求、产品经理分析以及代码审查反馈，
    编写完整、可运行的 Python 程序。

    重要要求：

    1. 最终完整代码必须放在且只放在一个 ```python ... ``` Markdown 代码块中
    2. 不要把代码拆成多个代码块
    3. 代码应能够直接保存为 output.py
    4. 必须保证代码语法完整
    5. 不要省略任何必要代码

    如果这是第一次开发：
    请根据用户需求和产品经理的需求分析完成代码。

    如果 CodeReviewer 返回 REVIEW_FAIL：
    1. 仔细阅读 CodeReviewer 提出的具体问题
    2. 根据问题修改上一版代码
    3. 必须重新输出修改后的完整代码
    4. 不允许只输出修改片段
    5. 修改后的完整代码仍然必须放在一个完整的 ```python ... ``` 代码块中

    请考虑：
    - 功能是否满足要求
    - 边界情况
    - 异常处理
    - 代码可读性
    - 代码健壮性

    完成代码后说“请代码审查员检查”。
    """
    return AssistantAgent(
        name = "Engineer",
        model_client = model_client,
        system_message = system_message,
        model_client_stream=True,
    )

# 代码审查员（CodeReviewer）
# 代码审查员的定义侧重于代码质量。安全性和规范性
# 它的系统消息详细列出了审查的重点和流程，确保了代码交付前的质量关卡
def create_code_reviewer(model_client):
    """创建代码审查员智能体"""
    system_message = """
    你是一位严格的代码审查专家。

    你需要同时检查：

    1. Engineer 最新生成的完整代码
    2. CodeExecutor 最新返回的真实执行结果
    3. 程序是否满足用户需求
    4. 是否存在运行错误
    5. 是否存在明显逻辑错误
    6. 是否存在重要的安全性或健壮性问题

    特别注意：

    CodeExecutor 的输出是真实运行结果，
    不能只相信 Engineer 对代码的描述。

    如果代码或运行结果存在问题：

    第一行必须回复：

    REVIEW_FAIL

    然后明确说明：
    - 出现了什么问题
    - Engineer 应该如何修改

    不要编写新的代码。

    如果代码正确、运行成功，而且满足用户要求：

    最终回复必须且只能是：

    REVIEW_PASS
    """
    return AssistantAgent(
        name = "CodeReviewer",
        model_client = model_client,
        system_message = system_message,
        model_client_stream=True,
    )

# 用户代理(UserProxy)
# UserProxyAgent 是一个特殊的智能体，它不依赖 LLM 进行回复，而是作为用户在系统中的代理
# 它的 description 字段清晰地描述了其职责，尤其重要的是，它负责在任务最终完成后发出 TERMINATE 指令，以正常结束整个协作流程
def create_user_proxy():
    """创建用户代理智能体"""
    return UserProxyAgent(
        name = "UserProxy",
        description="""用户代理，负责以下职责：
1. 代表用户提出开发需求
2. 执行最终的代码实现
3. 验证功能是否符合预期
4. 提供用户反馈和建议

完成测试后请回复 TERMINATE。"""
    )

# 定义团队协作流程
# 软件开发的流程是相对固定的 （需求 -> 编码 -> 审查 -> 测试），因此 RoundRobinGroupChat(轮询群聊)是理想的选择
# 我们按照业务逻辑顺序，将四个智能体加入到参与者列表中

# 真正控制整个团队的是这个函数，所有东西都是在这组装起来的
# 因为模型API请求不是瞬间完成的，所以用 async 网络请求天然适合异步
async def run_software_development_team():
    """初始化客户端和智能体"""
    print("🔧 正在初始化模型客户端...")

    # 先使用标准的 OpenAI 客户端进行测试
    # 先创建模型
    model_client = create_openai_model_client()

    print("👥 正在创建智能体团队...")
    try:
        # =====================================================
        # 第一阶段：ProductManager 进行需求分析
        # =====================================================

        print("\n👔 第一阶段：产品经理分析需求")
        print("=" * 60)

        product_manager = create_product_manager(model_client)

        # 现在暂时使用简单 Python 任务验证整个正式架构
        user_request = """
        请开发一个 Python 程序：

        计算 1 到 100 所有整数之和，并打印结果。

        要求：
        1. 使用 Python
        2. 程序完整可运行
        3. 不需要第三方库
        """
        # 把用户原始需求交给 ProductManager
        pm_response = await product_manager.on_messages(
            [
                TextMessage(
                    content=user_request,
                    source="user",
                )
            ],
            CancellationToken(),
        )
        print("\n---------- ProductManager ----------")
        print(pm_response.chat_message.content)

        # =====================================================
        # 第二阶段：Engineer + Executor + Reviewer 开发闭环
        # =====================================================

        print("\n🤖 第二阶段：进入自动开发闭环")
        print("=" * 60)

        engineer = create_engineer(model_client)
        code_reviewer = create_code_reviewer(model_client)

        # Docker 的工作目录
        work_dir = Path("agent_workspace")
        work_dir.mkdir(exist_ok=True)

        # 启动 Docker Executor
        async with DockerCommandLineCodeExecutor(
                image="python:3.12-slim",
                work_dir=work_dir,
                timeout=30,
        ) as docker_executor:
            # 创建 CodeExecutorAgent
            code_executor = create_code_executor(
                docker_executor
            )

            # 只有 CodeReviewer 最终严格回复 REVIEW_PASS 才结束
            termination = FunctionalTermination(
                reviewer_passed
            )

            # 开发团队
            development_team = RoundRobinGroupChat(
                participants=[
                    engineer,
                    code_executor,
                    code_reviewer,
                ],

                termination_condition=termination,

                # 最多允许三轮：
                # Engineer -> Executor -> Reviewer
                max_turns=9,
            )
            # 把“用户需求 + 产品经理分析”一起交给开发团队
            # 编排层有意识地把第一阶段的产物交给第二阶段
            development_task = f"""
            下面是用户的原始需求：
        
            {user_request}
        
            下面是 ProductManager 的需求分析：
        
            {pm_response.chat_message.content}
        
            现在请开始软件开发。
        
            工作流程：
        
            Engineer 编写完整代码
            → CodeExecutor 在 Docker 中执行
            → CodeReviewer 审查代码和真实执行结果
        
            如果 CodeReviewer 返回 REVIEW_FAIL：
            Engineer 必须根据审查意见修改完整代码，
            然后重新执行和审查。
        
            直到 CodeReviewer 返回 REVIEW_PASS。
            """
            # 启动开发团队
            result = await Console(
                development_team.run_stream(
                    task=development_task
                )
            )
        # =====================================================
        # 第三阶段：保存最终 Engineer 代码
        # =====================================================

        print("\n💾 正在保存最终代码...")

        save_engineer_code(
            result,
            filename="output.py",
        )

        print("\n" + "=" * 60)
        print("✅ 软件开发流程结束")
        print(f"停止原因：{result.stop_reason}")

        return result
    finally:
        await model_client.close()




# 主程序入口
if __name__ == "__main__":
    try:
        # 运行异步协作流程
        result = asyncio.run(run_software_development_team())

        print("\n📋 协作结果摘要：")
        print("- ProductManager：需求分析")
        print("- Engineer：代码实现")
        print("- CodeExecutor：Docker 执行")
        print("- CodeReviewer：代码与运行结果审查")
        print(f"- 停止原因：{result.stop_reason}")

    except ValueError as e:
        print(f"❌ 配置错误：{e}")
        print("请检查 .env 文件中的配置是否正确")
    except Exception as e:
        print(f"❌ 运行错误：{e}")
        import traceback

        traceback.print_exc()