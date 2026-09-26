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

    # 和上面那个抽象方法一样
    # 意思是每一个具体的 Tool 不但必须会执行，还必须告诉框架自己需要哪些参数
    @abstractmethod
    def get_parameters(self) -> list[ToolParameter]:
        """返回工具参数定义"""
        pass

    def to_openai_schema(self) -> dict[str,Any]:
        """转换成 OpenAI Function Calling 使用的 Schema"""
        # parameter 里面的意思是 如果你决定调用 calculator，那你必须安按照下面规定的结构提供参数
        # 这里面使用的是 JSON Schema
        # 所以严格来说，我们现在制定的“OpenAI Schema” 其实包含两层
        # 外层是 OpenAI 规定的工具描述格式
        # parameters 里面才是真正的 JSON Schema 参数描述
        parameters = self.get_parameters()

        properties = {}
        required = []

        for parameter in parameters:
            # 1. 当前参数的基本描述
            # 因为我们还要继续往这个参数说明里加东西
            prop = {
                'type':parameter.type,
                'description':parameter.description,
            }

            # 2. 如果参数有默认值
            if parameter.default is not None:
                prop['description'] = (
                    f'{parameter.description}'
                    f'(默认：{parameter.default})'
                )
            # 3. 如果参数是数组
            if parameter.type == 'array':
                prop['items'] = {'type': 'string'}

            # 4. 放入 properties
            properties[parameter.name] = prop

            # 5. 收集必填参数
            if parameter.required:
                required.append(parameter.name)
        # 6. 最终生成 Schema
        return {
            # 这是工具类型
            "type" : "function",
            "function" : {
                "name" : self.name,
                'description' : self.description,
                "parameters" : {
                    # 这里用 object 是因为一次函数调用的参数整体，会表示成一个 JSON 对象
                    # 可用理解成 Json object ≈ Python dict
                    # 于是 “type”:"object" 就是在说 calculator 的所有参数组合起来，要是一个键值对对象
                    "type" : "object",
                    # properies 可用直接理解成: 这个参数对象里面允许有哪些字段
                    # 这里面的 type 是参数的数据类型
                    "properties" : properties,
                    # 意思是调用这个函数时，expression 是必填参数
                    "required" : required,
                }
            }
        }

    def run(
            self,
            # dict 天然支持多个参数
            parameters : dict[str,Any]
    ) -> str:
        """
        新版接口：必须接收参数字典执行工具
        当前阶段作为兼容层
        内部暂时调用旧的 execute()
        所以当前 run()像一个转接头
        """
        # 这是为了让 BaseTool 知道：字典里的哪个key才是这个工具真正需要的参数
        tool_parameters = self.get_parameters()

        # 因为现在旧接口只有 execute(input_data:str)
        # 所以很自然只能接收一个字符串
        if len(tool_parameters) != 1:
            raise ValueError(
                "当前兼容版本的 run()"
                "暂时只支持单参数工具"
            )
        parameter_name = tool_parameters[0].name

        if parameter_name not in parameters:
            raise ValueError(
                f"缺少工具参数：{parameter_name}"
            )

        value = parameters[parameter_name]

        return self.execute(str(value))



    def __str__(self) -> str:
        return f"{self.name}:{self.description}"

