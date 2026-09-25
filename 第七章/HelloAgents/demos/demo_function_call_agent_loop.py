from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.tools.calculator import CalculatorTool
from hello_agents.agents.function_call_agent import FunctionCallAgent

load_dotenv()

llm = HelloAgentsLLM()

agent = FunctionCallAgent(
    name = "Function Call 助手",
    llm = llm,
    tools = [CalculatorTool()],
    max_steps=5
)

question = '''
请分别计算：

1. 23 * 17 + 5
2. sqrt(144)

最后告诉我两个结果。
'''
result = agent.run(question)

print("\n========== 最终回答 ==========")
print(result)