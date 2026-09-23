'''Agent 抽象类'''
# 这里的 ABC 指的是 Abstract Base Classes 也就是抽象基类
from abc import ABC ,abstractmethod

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.core.message import Message
from hello_agents.core.config import Config

# Agent 不是拿来直接创建具体智能体的，它主要是拿来规定”所有Agent应该长什么样“
# 这和 class Message(BaseModel) 很不同，Message直接创建对象很正常
# 但是 Agent 我们不希望直接拿来用，因为”一个Agent“太抽象了，不清楚到底是 ReAct,Relrction...
# 所以 Agent 更像 接口规范 + 公共能力
class Agent(ABC):
    '''所有 Agent 的基类'''
    # 说明每个 Agent 至少可以拥有 name,llm,system_prompt,config
    def __init__(
             self,
             name: str,
             llm: HelloAgentsLLM,
             system_prompt: str|None = None,
             config: Config|None = None,
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        # 用户如果自己提供就用用户的，否则就默认配置
        self.config = config or Config()

        # list[Message] 这是一个列表，而且列表里面装的是 Message 对象
        # 这就是 Agent 的对话历史
        # _history 表示一种约定，这是 Agent 内部属性，外面不能随便修改
        self._history : list[Message] = []

    # 意思是 所有继承 Agent 的具体子类，都必须自己实现 run()
    # 因为不同 Agent 的逻辑完全不同，所以父类无法写一个统一的具体算法，但是可以统一要求
    @abstractmethod
    def run(self,input_text: str) -> str:
        '''所有具体 Agent 都必须实现 run()'''
        pass

    def add_message(self,message: Message):
        '''添加一条历史消息'''
        self._history.append(message)

    def clear_history(self):
        '''清空历史记录'''
        self._history.clear()

    # 细节：返回的是 _history.copy()
    # 因为如果 history 和 agent._history 是同一个列表，那么用户执行 .clear时，会把 Agent 内部的历史也清理掉
    # 所以给用户一个副本
    def get_history(self) -> list[Message]:
        '''获得历史记录'''
        return self._history.copy()

    def __str__(self) -> str:
        return f"Agent(name={self.name})"

