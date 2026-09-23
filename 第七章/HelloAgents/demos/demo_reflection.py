from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.agents.reflection_agent import ReflectionAgent


load_dotenv()


llm = HelloAgentsLLM()


general_agent = ReflectionAgent(
    name="通用反思助手",
    llm=llm
)

code_prompts = {
    "initial": """
你是一名 Python 程序员。

请完成下面的编程任务：

{task}

请给出 Python 代码。
""",

    "reflect": """
你是一名代码审查员。

原始任务：
{task}

当前代码：
{content}

请重点检查：

1. 代码是否正确
2. 是否存在边界条件问题
3. 时间复杂度是否合理
4. 是否有可以简化的地方

如果代码已经很好，请回答“无需改进”。
""",

    "refine": """
你是一名 Python 程序员。

请根据代码审查意见修改代码。

原始任务：
{task}

原代码：
{last_answer}

审查意见：
{feedback}

请输出改进后的代码。
"""
}

code_agent = ReflectionAgent(
    name="代码反思助手",
    llm=llm,
    custom_prompt=code_prompts,
)



result = code_agent.run(
    """
编写一个 Python 函数，
输入整数 n，
返回 1 到 n 的整数之和。
"""
)

print("\n========== 最终结果 ==========")
print(result)