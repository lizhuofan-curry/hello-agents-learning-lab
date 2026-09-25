import json

from typing import Any

from hello_agents.core.agent import Agent
from hello_agents.tools.base import BaseModel, BaseTool


class FunctionCallAgent(Agent):
    """ 基于原生 Function Calling 的 Agent """
    # 这个函数把以前的 response = llm._client.chat.completions.create封装起来了
    # 这就是所谓的 封装底层 API 细节
    # 假如以后底层参数需要修改，只需改 _invoke_with_tools ，不需要满项目搜索 client.chat.completions.create
    # 能力 1 : 负责和支持 tools 的 LLM API 通信
    def _invoke_with_tools(
            self,
            messages:list[dict[str,Any]],
            tools:list[dict[str,Any]],
            tool_choice='auto',
    ):
        '''调用支持 Function Calling 的底层模型'''
        # getattr 可以理解成:尝试从 self.llm 里寻找 "_client"
        # 找到了就返回它，找不到就返回 None
        client = getattr(
            self.llm,
            '_client',
            None
        )

        # 如果没有找到 client 就能主动报一个看得懂的错误
        if client is None:
            raise RuntimeError(
                'HelloAgentsLLM 没有正确初始化底层客户端'
            )

        return client.chat.completions.create(
            model = self.llm.model,
            messages = messages,
            tools = tools,
            tool_choice = tool_choice,
            temperature = self.llm.temperature
        )

    # 能力 2: 负责 JSON 字符串 -> Python dict
    def _parse_function_call_arguments(
            self,
            # 刚刚 tool.call.function.arguments 实际上是 str
            arguments:str
    ) -> dict[str,Any]:
        '''解析模型返回的 Function Call 参数'''
        # 处理极端情况
        if not arguments:
            return {}
        # LLM 返回的参数理论上应该是合法的JSON,但是作为框架，不能假设永远正确
        try:
            # 把 str 变成 dict
            parsed_arguments = json.loads(arguments)

        except json.JSONDecodeError as e:
            # raise ... from e 表示现在抛出一个更好理解的新错误，但保留原始错误作为原因
            raise ValueError(
                f'Function Call 参数是不合法的 JSON : {arguments}'
            ) from e

        if not isinstance(parsed_arguments,dict):
            raise ValueError(
                "Function Call 参数解析后必须是字典"
            )

        return parsed_arguments

    # 能力 3:把工具对象转换为 Schema，继续封装
    def _build_tool_schemas(
            self,
            tools:list[BaseTool]
    ) -> list[dict[str,Any]]:
        '''把工具对象转换为 OpenAI Function Calling Schema'''
        # 它虽然只有几行，但负责的是一个很明确的转换 Python Tool 对象 -> OpenAI Tool Schema
        schemas = []

        for tool in tools:
            schema = tool.to_openai_schema()
            schemas.append(schema)

        return schemas

    # 能力 4： 从模型返回的消息中提取文本内容
    # 把 SDK 返回格式的小细节藏进 Agent 内部
    # 而不用管底层 content 是 None还是str或者有没有值
    def _extract_message_content(
            self,
            message:Any
    )-> str:
        '''从模型返回的消息中提取文本内容'''
        # 尝试找 message.content 找到了就返回 content，没找到就返回 None
        content = getattr(
            message,
            'content',
            None
        )
        if content is None:
            return ""

        if isinstance(content,str):
            return content

        return str(content)

    # 能力 5：是在让“模型给出的参数类型”对齐“工具声明的参数类型”
    # 这种设计叫 防御性编程 (defensive programming)
    # 不要假设所有输入永远完美，而是尽量把一些常见格式问题修正掉
    # 本质就是一个工具入口前的参数清洗器
    def _convert_parameter_types(
            self,
            tool:BaseTool,  # 给我一个工具 Tool
            param_dict : dict[str,Any]  # 以及模型传过来的参数 param_dict
    ) -> dict[str,Any]: # 返回 类型修正后的参数字典
        '''根据工具参数定义转换参数类型'''
        # 这里先问工具 “你需要什么参数”
        tool_parameters = tool.get_parameters()

        param_types = {}

        # 注意这时候 tool_parameters 是 list[ToolParameters] 里面放的是一个个对象
        for parameter in tool_parameters:
            # 这一步是在做格式整理
            # 把它整理成一个更容易查找的字典
            # 因为以后拿到 key = "count" 完美可以直接 param_types['count'] 得到 integer
            # 这就是 参数名 -> 参数类型的快速查询表，后面不需要一个个遍历了
            param_types[parameter.name] = parameter.type
        # 创建这个表是因为不想直接修改 param_dict 的原始参数
        # 假设 param_dict {'count' : '5'} ，我们希望它留下不动，再创建 converted_dict{'count': 5}
        # 这样原始输入保存原样，转换结果变成新字典，这种写法通常更安全
        converted_dict = {}

        for key,value in param_dict.items():
            # 如果模型传来的这个参数，工具根本没有声明，那就跳过
            if key not in param_types:
                # 工具没声明这个参数，我不知道该怎么转换，所以先保留原值
                converted_dict[key] = value
                continue

            param_type = param_types[key]

            # 接下来进入真正转换部分
            try:
                if param_type == "integer":
                    # 先检查 value 是不是字符串
                    if isinstance(value,str):
                        converted_dict[key] = int(value)
                    else :
                        converted_dict[key] = value
                # 一般来说 JSON Schema 里面的 number 对应 Python 里面的 float
                elif param_type == "number":
                    if isinstance(value,str):
                        converted_dict[key] = float(value)
                    else:
                        converted_dict[key] = value
                elif param_type == "boolean":
                    if isinstance(value,str):
                        # 这里不能直接写 bool("False")
                        # 在Python中，因为只要字符串非空，基本就是 True
                        converted_dict[key] = (value.lower() in ('true','1','yes'))
                    else:
                        converted_dict[key] = bool(value)
                else:
                    # 这里是留给 string 走的
                    converted_dict[key] = value
            except (ValueError,TypeError):
                converted_dict[key] = value
        return converted_dict

    # 因为此时的 FunctionCallAgent 是继承了 Agent的
    # 而 Agent 里面有一个 @abstractmethod 抽象方法，所以必须实现 run()
    def run(self,input_text: str) -> str:
        '''暂时留到下一版实现'''
        return "FunctionCallAgent V1"