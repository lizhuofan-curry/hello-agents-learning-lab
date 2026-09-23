from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.agents.plan_solve_agent import PlanAndSolveAgent

load_dotenv()

llm = HelloAgentsLLM()

agent = PlanAndSolveAgent(
    name = '规划助手',
    llm = llm,
)

question = """
一个水果店周一卖出了15个苹果。
周二卖出的苹果数量是周一的两倍。
周三卖出的数量比周二少5个。
请问这三天总共卖出了多少个苹果？
"""

plan = agent._make_plan(question)

print("\n========== 解析后的计划 ==========")

print(plan)


print("\n========== 数据类型 ==========")

print(type(plan))

print("\n========== 逐个步骤 ==========")

for i,step in enumerate(plan,1):
    print(f'步骤 {i}: {step}')

