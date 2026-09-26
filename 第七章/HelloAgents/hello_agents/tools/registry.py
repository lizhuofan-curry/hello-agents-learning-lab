"""工具注册表"""
from hello_agents.tools.base import BaseTool
# Callable 可以简单理解成这个东西是一个可以被调用的函数
# 例如 def say_hello(name) 就是Callable
from typing import Any,Callable

class ToolRegistry:
    """统一管理所有工具"""

    def __init__(self):
        # 注意 key 是 str,value是 BaseTool,也就是真正的 Python 对象
        # 所以 ToolRegistry 本质上就是一个“工具名字 -> 工具对象”的映射表
        self._tools : dict[str,BaseTool] = {}

        # 这个字典用来存普通的Python函数
        '''
        例如：
        {
        "say_hello": {
            "description": "向用户打招呼",
            "func": say_hello
            }
        }
        因为除了函数本身，我们还想保存工具描述 description
        '''
        self._functions : dict[
            str,
            dict[str,Any]
        ] = {}

    def register_tool(self,tool:BaseTool):
        '''注册一个工具'''
        # 所谓“工具注册”其实就是 把一个工具对象按名字登记到一个统一字典里
        if tool.name in self._tools:
            print(f"警告：工具 '{tool.name}'已存在，将被覆盖")

        self._tools[tool.name] = tool
        print(f"工具 '{tool.name}' 注册成功")

    def register_function(
            self,
            name:str,
            description:str,
            # 表示这个函数接收一个 str -> 返回一个 str
            # 所以可以理解成 (str) -> str
            # function：say_hello 不加括号表示把“函数本身”交给 Resgistry 保存
            # 而 say_hello() 表示立即执行这个函数，把执行结果叫过去
            # 我们需要保存的是函数，而不是函数的执行结果
            func:Callable[[str],str]
    ):
        '''直接注册一个普通函数作为工具'''
        # 适用于简单,快速工具
        if name in self._functions:
            print(f"警告：函数工具 '{name}' 已存在，将被覆盖")

        self._functions[name] = {
            'description': description,
            'func':func
        }
        print(f"函数工具 '{name}' 注册成功")

    def get_tool(self,tool_name: str) -> BaseTool|None:
        '''根据名字寻找工具'''
        return self._tools.get(tool_name)

    def execute_tool(
            self,
            tool_name:str,
            input_data:str | dict[str,Any]  # 表示 input_data 可以是这两种类型之一
    ) -> str:
        '''执行工具'''
        # 1. 先找 Tool 对象
        tool = self.get_tool(tool_name)

        if tool is not None:
            if isinstance(input_data,dict):
                return tool.run(input_data)

            return tool.execute(input_data)

        # 2. 再找普通函数
        function_info = self._functions.get(tool_name)

        if function_info is not None:
            func = function_info['func']

            if isinstance(input_data,dict):
                return ('错误：普通函数工具''当前只支持字符串参数')

            return func(input_data)

        # 3. 都没有找到
        return(f"错误，找不到工具 {tool_name}")

    def list_tools(self) -> list[str]:
        '''返回所有已注册工具名称'''
        return list(self._tools.keys())

    # 这里是给 LLM 看的，因为 LLM 并不知道有哪些工具
    # 所以后面的 ReActAgent 在 Prompt 里面告诉它，模型才能判断调用哪个工具
    # 这其实是在解决 Agent 如何发现 Resgistry 里有哪些工具
    # 这对于 ReAct 架构来说很重要
    def get_tools_description(self) -> str:
        '''获取所有可用工具的描述'''
        # 先准备一个空列表，后面不断往里面装描述部分
        descriptions = []

        # BaseTool 工具
        # Too直接用 value 拿到的是对象
        for tool in self._tools.values():
            descriptions.append(
                f"- {tool.name} : {tool.description}"
            )

        # 普通函数工具
        # 这里用 items ,因为我们既需要name又需要info
        for name,info in self._functions.items():
            descriptions.append(
                f'- {name} : {info["description"]}'
            )

        if not descriptions:
            return '暂无可用工具'

        return "\n".join(descriptions)