'''Reflection Agent'''

from hello_agents.core.agent import Agent
from hello_agents.core.message import Message
INITIAL_PROMPT = """
请根据下面的任务给出一个完整回答。

任务：
{task}
"""


REFLECT_PROMPT = """
请仔细检查下面的回答。

原始任务：
{task}

当前回答：
{content}

请指出这个回答存在的问题，
并给出具体的改进建议。

如果已经很好，请回答“无需改进”。
"""
REFINE_PROMPT = """
请根据反思意见改进下面的回答。

原始任务：
{task}

上一版回答：
{last_answer}

反思意见：
{feedback}

请针对反思意见进行修改，
给出一份完整、准确、更加严谨的最终回答。

只需要输出修改后的最终回答。
"""
class ReflectionAgent(Agent):
    '''具有反思能力的 Agent'''

    def run(self,input_text:str) -> str:

        # 1. 生成初始回答
        initial_prompt = INITIAL_PROMPT.format(task=input_text)

        initial_messages = [
            {
                'role' : 'user',
                'content' : initial_prompt,
            }
        ]

        initial_answer = self.llm.invoke(initial_messages)

        print('\n============= 初始回答 ================')
        print(initial_answer)

        # 2. 对初始回答进行反思
        reflect_prompt = REFLECT_PROMPT.format(
            task = input_text,
            content = initial_answer,
        )

        reflect_messages = [
            {
                'role' : 'user',
                'content': reflect_prompt,
            }
        ]

        feedback = self.llm.invoke(reflect_messages)

        print("========= 反思结果 ============")
        print(feedback)

        # 根据反思结果改进回答
        refine_prompt = REFINE_PROMPT.format(
            task = input_text,
            last_answer = initial_answer,
            feedback = feedback
        )

        refine_messages = [
            {
                'role' : 'user',
                'content': refine_prompt
            }
        ]
        final_answer = self.llm.invoke(refine_messages)

        print('\n============== 改进后的回答 =============')
        print(final_answer)

        # 补上 Agent 的历史记录
        self.add_message(
            Message(
                role = 'user',
                content = input_text
            )
        )
        self.add_message(
            Message(
                role = "assistant",
                content=final_answer
            )
        )

        return final_answer