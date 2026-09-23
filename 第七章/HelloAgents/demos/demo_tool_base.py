from hello_agents.tools.base import BaseTool

class EchoTool(BaseTool):

    def execute(self,input_data: str) -> str:
        return f"工具收到：{input_data}"


tool= EchoTool(
    name='Echo',
    description="原样返回输入内容"
)

print(tool)

result = tool.execute("你好")

print(result)
