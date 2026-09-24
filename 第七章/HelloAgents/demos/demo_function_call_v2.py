import json

from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.tools.calculator import CalculatorTool

load_dotenv()

# 1.创建 LLM
llm = HelloAgentsLLM()

# 2.创建计算器工具
calculator = CalculatorTool()

# 3.转换成 OpenAI Tool Schema
tools = [calculator.to_openai_schema()]

# 4.用户消息
messages = [
    {
        'role':'user',
        'content':"请计算 23 * 17 + 5"
    }
]

# 5.调用模型消息
response = llm._client.chat.completions.create(
    model = llm.model,
    messages=messages,
    tools = tools,
    tool_choice='auto',
    temperature=llm.temperature,
)

# 6.获取模型消息
message = response.choices[0].message

print("=============== 模型文本回答 ================")
print(message.content)

print('\n============== Tool Calls ===============')
print(message.tool_calls)

# 7.处理 Tool Call
if message.tool_calls:
    for tool_call in message.tool_calls:

        print("\n=========== 模型请求调用工具 ==============")

        print("工具调用 ID:")
        print(tool_call.id)

        print("\n工具名称:")
        print(tool_call.function.name)

        print('\n原始 arguments :')
        print(tool_call.function.arguments)

        print("\n原始 arguments 类型：")
        print(type(tool_call.function.arguments))

        # 8. JSON 字符串 -> Python 字典
        arguments = json.loads(
            tool_call.function.arguments
        )

        print("\n解析后的 arguments :")
        print(arguments)

        print('\n解析后的 arguments 类型 :')
        print(type(arguments))

        # 9. 从字典中取出 expression
        expression = arguments['expression']

        print('\n提取出的 expression:')
        print(expression)

        # 10. 真正执行 CaculatorTool
        result = calculator.execute(expression)

        print('\n============ 工具执行结果 =============')
        print(result)