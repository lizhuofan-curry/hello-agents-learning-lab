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

print("========== message.content ==========")
print(message.content)


print("\n========== message.tool_calls ==========")
print(message.tool_calls)

'''
========== message.content ==========

========== message.tool_calls ==========
[ChatCompletionMessageFunctionToolCall
(id='call_00_o5n0R9mXkzWSiaj3IFaw7094',
 function=Function(arguments='{"expression": "23 * 17 + 5"}', name='calculator'), type='function', index=0)]

这次返回结果和之前的 V1 几乎一样，虽然外部效果没变化，但代码结构发生了变化
以前: Demo -> 直接操作 OpenAI SDK
现在: Demo -> FunctionCallAgent -> _invoke_with_tools -> OpenAI SDK
'''