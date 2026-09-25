from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.tools.calculator import CalculatorTool
from hello_agents.agents.function_call_agent import FunctionCallAgent

load_dotenv()

llm = HelloAgentsLLM()

calculator = CalculatorTool()

agent = FunctionCallAgent(
    name = "Function Call 助手",
    llm = llm,
)

messages = [
    {
        'role':'user',
        'content':'请计算 23 * 17 + 5'
    }
]

tools = [calculator.to_openai_schema()]

response = agent._invoke_with_tools(
    messages=messages,
    tools=tools,
)

message = response.choices[0].message

print("================ message.content ==============")
print(message.content)

print("\n=============== message.tool_calls ==============")
print(message.tool_calls)

if message.tool_calls:
    for tool_call in message.tool_calls:

        print("\n========= 原始参数 ============")

        raw_arguments = tool_call.function.arguments

        print(raw_arguments)
        print(type(raw_arguments))

        print('\n============ Agent 解析参数 ===============')
        arguments = agent._parse_function_call_arguments(raw_arguments)

        print(arguments)
        print(type(arguments))

        print("\n=========== expression ===============")
        print(arguments["expression"])
