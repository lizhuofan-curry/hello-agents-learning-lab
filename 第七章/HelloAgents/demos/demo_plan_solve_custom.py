from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.agents.plan_solve_agent import PlanAndSolveAgent

load_dotenv()

llm = HelloAgentsLLM()

math_prompts = {
    "planner": """
你是一名数学问题规划专家。

请把下面的问题拆解成若干个独立的计算步骤。

问题：
{question}

只负责制定计划，不要提前计算答案。

严格按照 Python 列表输出：

["步骤1", "步骤2", "步骤3"]

不要输出其他内容。
""",

    "executor": """
你是一名数学计算专家。

原始问题：
{question}

完整计划：
{plan}

已经完成的步骤：
{history}

当前步骤：
{current_step}

请根据已有结果完成当前计算步骤。
只输出当前步骤需要的计算过程和结果。
"""
}

agent = PlanAndSolveAgent(
    name = "数学规划助手",
    llm = llm,
    custom_prompts=math_prompts
)
question = """
一个长方形的长是12米，宽是8米。
现在长增加3米，宽减少2米。
请问新的长方形面积是多少？
"""
result = agent.run(question)
print("\n========== 最终结果 ==========")
print(result)


print("\n========== 对话历史 ==========")

for message in agent.get_history():
    print(message)

