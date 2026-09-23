'''Reflection Agent'''

from hello_agents.core.agent import Agent

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

        # V1 暂时返回初始回答
        return initial_answer