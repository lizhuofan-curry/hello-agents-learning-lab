from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.tools.calculator import CalculatorTool
from hello_agents.agents.function_call_agent import FunctionCallAgent

load_dotenv()

llm = HelloAgentsLLM()

calculator = CalculatorTool()

agent = FunctionCallAgent(
    name = 'Function Call 助手',
    llm = llm,
)

# 注意:这里放的是”真正的工具对象“
tool_objects = [calculator]

# 交给 Agent 自动转换
tool_schemas = agent._build_tool_schemas(tool_objects)

print('=========== Python 工具对象 ===============')
print(tool_objects)

print('\n=============== 构建后的 Tool Schema ===============')
for schema in tool_schemas:
    print(schema)

message = [
    {
        "role":"user",
        "content":"请计算 23 * 17 + 5"
    }
]

response = agent._invoke_with_tools(
    messages=message,
    tools=tool_schemas,
)

message = response.choices[0].message

print('\n============ Tool Calls =================')
print(message.tool_calls)

if message.tool_calls:
    for tool_call in message.tool_calls:
        arguments = agent._parse_function_call_arguments(
            tool_call.function.arguments
        )

        print('\n=============== 解析后的参数 ============')
        print(arguments)