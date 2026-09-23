'''消息系统'''
'''统一数据长什么样'''
# 处理日期时间
from datetime import datetime
# Any 是什么类型都可以，Literal:只能取我明确列出来的这些值
from typing import Any,Literal

from pydantic import BaseModel,Field

# 相当于我们自己创建了一个新的类型名字
MessageRole = Literal[
    'user',
    'assistant',
    'system',
    'tool'
]

# Message 继承了 Pydantic 提供的 BaseModel,于是 Pydantic 会开始帮我们做很多事情
class Message(BaseModel):
    '''HelloAgents 内部统一的消息格式'''
    # 这里面都不用写 __init__ , 因为 BaseMode在背后干完了
    content : str
    role : MessageRole

    # 时间戳，记录这条消息什么时候产生，datetime.now()获得当前时间
    # 一条消息产生时，默认时间本来就在“现在”
    # 如果用户没有给 timestamp,那就调用 datatime.now 帮我生成一个默认值
    # 注意不是 datetime.now() 因为现在不是立刻获取时间，而是把获取当前时间这个函数交给 Pydantic
    timestamp : datetime = Field(default_factory=datetime.now)
    # 框架以后可能还想知道 ： 这个消息来自哪个模型，消耗了多少 token,是不是重要消息，是不是工具产生的，属于哪个对话
    # 可以理解成这条消息的附加说明，而且希望它自动是 {} 空字典
    metadata : dict[str,Any] = Field(default_factory=dict)

    # 把 Message 对象 翻译成 dict
    def to_dict(self) -> dict[str,str] :
        '''转换为 LLM API 使用的消息格式'''
        # timestamp,metadata 是我们自己框架信息，真正发送模型时，只摘出它需要的部分
        return {
            'role':self.role,
            'content':self.content,
        }
    # __str__() 是 Python 的特殊方法，它决定 print(message) 时显示说明
    def __str__(self) -> str:
        return f"[{self.role}] {self.content}"

