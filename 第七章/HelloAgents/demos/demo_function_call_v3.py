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
# 第一次调用 LLM
response = llm._client.chat.completions.create(
    model = llm.model,
    messages=messages,
    tools = tools,
    tool_choice='auto',
    temperature=llm.temperature,
)

# 6.获取模型消息
message = response.choices[0].message
print("========== 第一次模型返回 ==========")

print("文本内容:")
print(message.content)

print("\nTool Calls:")
print(message.tool_calls)

# 保存 assistant 的工具调用请求
if message.tool_calls:
    assistant_message = {
        'role': 'assistant',
        'content': message.content,
        'tool_calls': []
    }

    for tool_calls in message.tool_calls:
        assistant_message['tool_calls'].append(
            {
                'id': tool_calls.id,
                'type': tool_calls.type,
                'function': {
                    'name': tool_calls.function.name,
                    'arguments': tool_calls.function.arguments
                }
            }
        )
    # 正在把模型第一轮产生的“工具调用请求”保存进上下文
    messages.append(assistant_message)

    # 执行所有 Tool Call
    for tool_call in message.tool_calls:
        arguments = json.loads(tool_call.function.arguments)

        expression = arguments['expression']

        result = calculator.execute(expression)

        print('\n============= 工具执行结果 ===============')
        print(result)

        # 把工具结果交给模型
        # Tool Message 在Function Calling 闭环里专门承载工具执行结果的角色
        tool_message = {
            'role': 'tool',
            'tool_call_id': tool_call.id,
            'content': str(result)
        }

        messages.append(tool_message)

        # 第二次调用 LLM
        final_response = llm._client.chat.completions.create(
            model=llm.model,
            messages=messages,
            tools=tools,
            tool_choice='auto',
            temperature=llm.temperature,
        )

        final_message = final_response.choices[0].message

        print("\n============ 最终模型回答 ===============")
        print(final_message.content)





