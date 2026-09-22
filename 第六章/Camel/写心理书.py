from colorama import Fore
'''
CAMEL核心，也是全程序最重要的一行，意思是 双 Agent 社会的管理器
官方源码中确实维护了 user_agent 和 assistant_agent,同时还维护各自的System Message
所以应该把 RolePlay 理解成建立一个 Agent Society
'''
from camel.societies import RolePlaying
from camel.utils import print_text_animated

# 创建一个 CAMEL 能调用的模型对象
from camel.models import ModelFactory
from camel.types import ModelPlatformType

from dotenv import load_dotenv
import os

# 读取模型配置
load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL_ID")

# 检查环境变量，避免后面报一些不好理解的 API 错误
if not LLM_API_KEY:
    raise ValueError("没有读取到 LLM_API_KEY，请检查 .env 文件")

if not LLM_BASE_URL:
    raise ValueError("没有读取到 LLM_BASE_URL，请检查 .env 文件")

if not LLM_MODEL:
    raise ValueError("没有读取到 LLM_MODEL，请检查 .env 文件")

# 创建底层 LLM
model = ModelFactory.create(
    model_platform=ModelPlatformType.QWEN,
    model_type=LLM_MODEL,
    url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
)


task_prompt = """
创作一本关于"拖延症心理学"的短篇电子书，
目标读者是对心理学感兴趣的普通大众。

要求：

1. 内容科学严谨，基于实证研究
2. 语言通俗易懂，避免过多专业术语
3. 包含实用的改善建议和案例分析
4. 篇幅控制在8000-10000字
5. 结构清晰，包含引言、核心章节和总结
"""

# 这实际上会给这两个Agent 分别准备不同的 System Prompt
# 这也就是 Inception Prompting (中文叫 引导性提示)
'''
RolePlaying 源码中默认开启了 with_task_specify=True
它让模糊的任务变成更具体，更适合两个角色执行的任务，也就是说细化后的任务会直接替代原始的 task_prompt
所以这里实际上多了一个 TaskSpecifyAgent 作为会议前整理会议议题的人
'''
role_play_session = RolePlaying(
    # 负责执行问题，回答问题，提供专业知识
    assistant_role_name= '心理学家',
    # 负责规划，拆解，下达下一步指令
    user_role_name= '作家',
    task_prompt = task_prompt,
    # 这一个 model 可以给 RolePlaying 内部的多个 Agent 共用
    # 但是里面的 Agent 是两个不同的 ChatAgent 对象，因此维护各自的上下文，也就是有独立的聊天历史
    model= model,
    # 明确开启 TaskSpecifyAgent
    # 让它先把原始任务进一步具体化
    with_task_specify=True
)
print("\n========== ① 原始任务 ==========")
print(task_prompt)

print("\n========== ② TaskSpecifyAgent 细化后的任务 ==========")
print(role_play_session.specified_task_prompt)

print("\n========== ③ RolePlaying 最终使用的任务 ==========")
print(role_play_session.task_prompt)

print("\n========== ④ 心理学家的 System Message ==========")
print(role_play_session.assistant_sys_msg)

print("\n========== ⑤ 作家的 System Message ==========")
print(role_play_session.user_sys_msg)

# 开启角色创作
chat_turn_limit = 30
n = 0

# init_chat 不调用 LLM
# 它负责 reset  两个 Agent ,并构造第一条 Assitant Message
input_msg = role_play_session.init_chat()

while n < chat_turn_limit:
    n +=1
    print(f"\n{'=' * 20} 第 {n} 轮 {'=' * 20}")
    # 一次 step 内部：
    #
    # input_msg
    #     ↓
    # user_agent（作家）
    #     ↓
    # user_response
    #     ↓
    # assistant_agent（心理学家）
    #     ↓
    # assistant_response
    assistant_response,user_response = role_play_session.step(input_msg)

    # ----------- 先检查 Agent 是否异常终止 -----------
    if user_response.terminated:
        print(
            Fore.RED
            + f"作家 Agent 提前终止："
              f"{user_response.info.get('termination_reasons')}"
        )
        break

    if assistant_response.terminated:
        print(
            Fore.RED
            + f"心理学家 Agent 提前终止："
              f"{assistant_response.info.get('termination_reasons')}"
        )
        break

    # 输出这一轮两个 Agent 的回答
    print_text_animated(
        Fore.BLUE  + f"\n作家：\n\n{user_response.msg.content}\n"
    )
    print_text_animated(
        Fore.GREEN + f"\n心理学家：\n\n{assistant_response.msg.content}\n"
    )
    # 判断整个任务是否完成
    if "CAMEL_TASK_DONE" in user_response.msg.content:
        print(Fore.MAGENTA + "\n✅ 作家判断电子书任务已经完成！")
        break

    # 准备下一轮
    # 心理学家这一轮的输出成为下一轮作家收到的新输入
    input_msg = assistant_response.msg

print(Fore.YELLOW+ f"\n总共进行了 {n} 轮协作对话")
