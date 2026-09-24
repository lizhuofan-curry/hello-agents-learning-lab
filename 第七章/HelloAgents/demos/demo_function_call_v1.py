from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.tools.calculator import CalculatorTool

load_dotenv()

# 1.创建 LLM
llm = HelloAgentsLLM()

# 2.创建计算机工具
calculator = CalculatorTool()

# 3. 把计算器转换成 OpenAI Tool Schema
tools =[calculator.to_openai_schema()]

# 4.用户消息
messages = [
    {
        'role':'user',
        'content':'请计算 23 * 17 + 5'
    }
]

# 5.直接调用底层 OpenAI 客户端
# 为什么这次不用之前自己写的 invoke()
# 因为之前那一版没有 tools = ... 这个入口
# 所以这一版为了直接看清底层机制，我们暂时直接绕过自己封装发 invoke(),直接碰 API
# 之后写 FunctionCallAgent 时，再把这部分封装起来
response = llm._client.chat.completions.create(
    model = llm.model,
    messages = messages,
    tools = tools,
    tool_choice='auto',
    temperature=llm.temperature,
)

# 6.取出模型返回的消息
# 此时输出的为 None,不是出 bug了
# 而是在说“我暂时不回答用户，我想先调用 calculator”
message = response.choices[0].message

print("============== 模型文本回答 ==============")
print(message.content)

print("\n=============== tool_calls ===============")
print(message.tool_calls)

# 7. 如果模型决定调用工具：
if message.tool_calls:
    for tool_call in message.tool_calls:
        print("\n=========== 单个 Tool Call ===========")

        # id 是在解决工具请求和工具结果如何一一对应
        print('tool_call id:')
        print(tool_call.id)

        print('\n工具类型:')
        print(tool_call.type)

        print('\n工具名称:')
        print(tool_call.function.name)

        print("\n工具参数:")
        # 这个输出看起来像 dict，但实际上是 str
        # "{"expression": "23 * 17 + 5"}"
        print(tool_call.function.arguments)

