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

tool_objects = [calculator]

tool_schemas = agent._build_tool_schemas(tool_objects)

# 测试一 : 需要调用工具
messages = [
    {
        'role':'user',
        'content': '请计算 23 * 17 + 5'
    }
]

response = agent._invoke_with_tools(
    messages=messages,
    tools = tool_schemas
)

message = response.choices[0].message

content = agent._extract_message_content(message)

print("================ 测试1：数学问题 =======================")

# 注意这里输出的是 “” ，这里模型不是什么都没做
# 而是没有选择用自然语言回答，选择了发起工作调用
# 所以这一轮的回答不是放在 message.content里，而是 message.tool_calls里
print("提出的文本：")
print(repr(content))

print('Tool Calls:')
print(message.tool_calls)

# 测试2:不需要调用工具
messages = [
    {
        'role':'user',
        'content':'请用一句话解释什么是机器学习'
    }
]

response = agent._invoke_with_tools(
    messages=messages,
    tools = tool_schemas
)
message = response.choices[0].message

# 这属于典型的把 SDK 返回格式的小细节藏进 Agent 内部
content = agent._extract_message_content(message)

print("=================== 测试2：普通问题 ==================")

print("提取出的文本:")
print(content)

print('Tool Calls:')
print(message.tool_calls)
