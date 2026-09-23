from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.agents.plan_solve_agent import PlanAndSolveAgent

load_dotenv()

llm = HelloAgentsLLM()

agent = PlanAndSolveAgent(
    name="PlanAndSolve助手",
    llm=llm
)

question = """
一个水果店周一卖出了15个苹果。
周二卖出的苹果数量是周一的两倍。
周三卖出的数量比周二少5个。
请问这三天总共卖出了多少个苹果？
"""

result = agent.run(question)

print("\n========== 最终结果 ==========")
print(result)