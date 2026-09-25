import json

from typing import Any

from hello_agents.core.agent import Agent

class FunctionCallAgent(Agent):
    """ 基于原生 Function Calling 的 Agent """
    # 这个函数把以前的 response = llm._client.chat.completions.create封装起来了
    # 这就是所谓的 封装底层 API 细节
    # 假如以后底层参数需要修改，只需改 _invoke_with_tools ，不需要满项目搜索 client.chat.completions.create
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



    # 因为此时的 FunctionCallAgent 是继承了 Agent的
    # 而 Agent 里面有一个 @abstractmethod 抽象方法，所以必须实现 run()
    def run(self,input_text: str) -> str:
        '''暂时留到下一版实现'''
        return "FunctionCallAgent V1"