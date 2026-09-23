from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.agents.reflection_agent import ReflectionAgent


load_dotenv()


llm = HelloAgentsLLM()


agent = ReflectionAgent(
    name="Reflection助手",
    llm=llm
)


result = agent.run(
    "请解释什么是机器学习中的过拟合，并给出两个解决方法。"
)


print("\n========== 当前返回结果 ==========")
print(result)