from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.agents.function_call_agent import FunctionCallAgent
from hello_agents.tools.base import BaseTool,ToolParameter

class TestTool(BaseTool):
    def __init__(self):
        super().__init__(
            name = 'test_tool',
            description="参数类型转换测试工具"
        )

    def execute(self,input_data: str) -> str:
        return input_data

    def get_parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="count",
                type="integer",
                description="次数"
            ),
            ToolParameter(
                name="temperature",
                type="number",
                description="温度"
            ),
            ToolParameter(
                name="enabled",
                type="boolean",
                description="是否启用"
            ),
            ToolParameter(
                name="name",
                type="string",
                description="名称"
            )
        ]

load_dotenv()

llm = HelloAgentsLLM()

agent = FunctionCallAgent(
    name = 'Function Call助手',
    llm = llm,
)

tool = TestTool()

arguments = {
    'count':'5',
    'temperature':'3.14',
    'enabled':'True',
    'name' : '小明'
}

print("================ 转换前 ===============")
for key,value in arguments.items():
    print(
        key,
        "=",
        value,
        "类型:",
        type(value),
    )

converted = agent._convert_parameter_types(tool,arguments)

print("\n========== 转换后 ==========")

for key, value in converted.items():
    print(
        key,
        "=",
        value,
        "类型:",
        type(value)
    )