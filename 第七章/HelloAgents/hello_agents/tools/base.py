'''工具基类'''
'''
工具也需要基类，以后可能有 CaculaterTool,SearchTool,WeatherTool,DatabaseTool
他们内部干的事情完全不同，但是agent 不应该写 caculator.calculate(),search.search()
而是站在 Agent 的角度，我们希望全部统一成 tool.execute(input_data),
所以添加了统一接口
'''
from abc import ABC,abstractmethod
from typing import Any
from pydantic import BaseModel

class ToolParameter(BaseModel):
    '''描述一个工具参数'''
    name : str
    type : str
    description : str
    required : bool = True
    default : Any = None


# 意思是 所有 Tool 必须会 execute()
# 现在就是在重复使用一种框架设计思想
# 可以发现框架很大一部分就是在干：规定统一接口，然后允许下面自由实现
class BaseTool(ABC):
    '''所有工具的基类'''

    def __init__(
            self,
            name:str,   # 需要通过名字找到工具
            description:str,    # 告诉LLM 哪些工具能用
    ):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self,input_data: str) -> str:
        '''执行工具'''
        pass

    def __str__(self) -> str:
        return f"{self.name}:{self.description}"

