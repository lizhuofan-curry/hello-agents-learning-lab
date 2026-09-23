'''最简单的对话 Agent'''

from hello_agents.core.agent import Agent
from hello_agents.core.message import Message

# SimpleAgent 继承至 Agent ,所以 SimpleAgent 自动拥有 name,llm,system_prompt,config,_history
# 没有重新写 __init__() 因为可以直接使用父类 Agent 的 __init__()
class SimpleAgent(Agent):
    '''基础对话智能体'''
    def run(self,input_text:str) -> str:

        # self._history 是 Agent 长期保存的历史记录，里面装的是 Message 对象
        # 但是 message 是为了这一次调用 LLM 临时组装的数据，里面装的是 dict
        messages = []

        # 1.添加系统提示词
        # 注意这里的 system_prompt 没有加入 _history
        # 因为 system_prompt 为 Agent 固定设定
        # _history 记录的是实际对话过程
        if self.system_prompt:
            system_message = Message(
                role = "system",
                content = self.system_prompt
            )

            messages.append(system_message.to_dict())

        # 2. 添加历史消息
        # 先将之前对话的历史消息加入 message
        # 这就是多轮对话为什么能”记住“上一轮，并不是模型自己记住了，而是 Agent 每次把历史记录重新发给模型
        for message in self._history:
            messages.append(message.to_dict())

        # 3. 创建当前用户消息
        user_message = Message(
            role = 'user',
            content = input_text
        )
        messages.append(user_message.to_dict())

        # 4.调用大模型
        # 这里的 self.llm 就是我们创建 Agent 时传入的 HelloAgentLLM()
        response = self.llm.invoke(messages)

        # 5.创建模型回复信息
        assitant_message = Message(
            role = 'assistant',
            content = response
        )

        # 6.保存本轮对话
        self.add_message(user_message)
        self.add_message(assitant_message)

        # 7.返回模型回答
        return response


