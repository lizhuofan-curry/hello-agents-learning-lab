from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.agents.react_agent import ReActAgent
from hello_agents.tools.calculator import CalculatorTool
from hello_agents.tools.registry import ToolRegistry

load_dotenv()

# 1. 创建 LLM
llm = HelloAgentsLLM()

# 2. 创建工具注册表
registry = ToolRegistry()

# 3. 创建计算器
calculator = CalculatorTool()

# 4. 注册计算器
registry.register_tool(calculator)

# 5. 创建 ReAct Agent
agent = ReActAgent(
    name = 'ReAct助手',
    llm = llm,
    tool_registry= registry,
)

# 6. 提问
result = agent.run("请帮我准确计算 23 * 17 + 5")

print("\n ======== ReAct 输出 ===========")

print(result)