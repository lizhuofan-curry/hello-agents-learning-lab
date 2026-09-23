"""工具注册表"""
from hello_agents.tools.base import BaseTool

class ToolRegistry:
    """统一管理所有工具"""

    def __init__(self):
        # 注意 key 是 str,value是 BaseTool,也就是真正的 Python 对象
        # 所以 ToolRegistry 本质上就是一个“工具名字 -> 工具对象”的映射表
        self._tools : dict[str,BaseTool] = {}

    def register_tool(self,tool:BaseTool):
        '''注册一个工具'''
        # 所谓“工具注册”其实就是 把一个工具对象按名字登记到一个统一字典里
        if tool.name in self._tools:
            print(f"警告：工具 '{tool.name}'已存在，将被覆盖")

        self._tools[tool.name] = tool
        print(f"工具 '{tool.name}' 注册成功")

    def get_tool(self,tool_name: str) -> BaseTool|None:
        '''根据名字寻找工具'''
        return self._tools.get(tool_name)

    def execute_tool(
            self,
            tool_name:str,
            input_data:str
    ) -> str:
        '''根据名字找到工具并执行'''
        tool = self.get_tool(tool_name)

        if tool is None:
            return f"错误，找不到工具 '{tool_name}'"

        return tool.execute(input_data)

    def list_tools(self) -> list[str]:
        '''返回所有已注册工具名称'''
        return list(self._tools.keys())

    # 这里是给 LLM 看的，因为 LLM 并不知道有哪些工具
    # 所以后面的 ReActAgent 在 Prompt 里面告诉它，模型才能判断调用哪个工具
    def get_tools_description(self) -> str:
        '''生成所有工具的说明'''
        if not self._tools:
            return "暂无可用工具"

        descriptions = []

        for tool in self._tools.values():
            descriptions.append(
                f"-{tool.name} : {tool.description}"
            )
        return "\n".join(descriptions)