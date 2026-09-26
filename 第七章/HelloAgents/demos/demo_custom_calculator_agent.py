from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.tools.my_calculator import create_calculator_registry
'''这里真正演示的是 ToolRegistry + LLM 的简单集成流程'''

load_dotenv()

# 1. 创建 LLM
llm = HelloAgentsLLM()

# 2.创建工具注册表
registry = create_calculator_registry()

# 3.用户问题
# 这一步用户给的是自然语言问题
user_question = ("请帮我计算 sqrt(16) + 2 * 3")

print('=========== 用户问题 ===============')
print(user_question)

# 4.手动调用计算器工具
# 然后我们人工知道这是一道数学题，应该调用 my_calculator
# 注意这里有两件事都是程序员提前决定的
# 1.调用哪个工具
# 2.给工具什么参数
calc_result = registry.execute_tool('my_calculator', 'sqrt(16) + 2 * 3')

print('\n==================== 工具结果 ======================')
print(calc_result)

# 5. 把工具结果交给 LLM
final_messages = [
    {
        "role": "user",
        "content": (
            f"用户的问题是：{user_question}\n"
            f"计算工具得到的结果是：{calc_result}\n"
            "请根据计算结果，用自然语言回答用户。"
        )
    }
]

# 6.让 LLM 生成最终回答
print("\n========== LLM 最终回答 ==========")

for chunk in llm.think(final_messages):
    print(chunk, end='', flush=True)

print()