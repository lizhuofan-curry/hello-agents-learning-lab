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
    # 因为此时的 FunctionCallAgent 是继承了 Agent的
    # 而 Agent 里面有一个 @abstractmethod 抽象方法，所以必须实现 run()
    def run(self,input_text: str) -> str:
        '''暂时留到下一版实现'''
        return "FunctionCallAgent V1"