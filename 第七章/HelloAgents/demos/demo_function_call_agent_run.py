from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.tools.calculator import CalculatorTool
from hello_agents.agents.function_call_agent import FunctionCallAgent

load_dotenv()

llm = HelloAgentsLLM()

agent = FunctionCallAgent(
    name = "Function Call 助手",
    llm = llm,
    tools=[CalculatorTool()]
)

result = agent.run("请计算 23 * 17 + 5")

print("\n============= 最终回答 ==================")
print(result)

print('\n============= 对话历史 ===================')
for message in agent.get_history():
    print(message)