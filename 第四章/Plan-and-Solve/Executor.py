
from llm_client import HelloAgentsLLM

# 在规划器(Planner) 生成了清晰的行动蓝图后，我们就需要一个执行器(Executor)来逐一完成计划中的任务
# 执行器不仅负责调用大模型来解决每个子问题，还承担着一个至关重要的角色：状态管理
# 它必须记录每一步的执行结果，并将其作为上下文提供给后续步骤

'''
执行器的提示词与规划器不同，它的目标不是分解问题
而是在已有上下文的基础上，专注解决当前这一个步骤
'''

EXECUTOR_PROMPT_TEMPLATE = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决“当前步骤”，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对“当前步骤”的回答:
"""

# 将执行逻辑封装到 Executor 类中，这个类将循环遍历计划，调用 LLM,并维护一个历史状态
class Executor:
    def __init__(self,llm_client):
        self.llm_client = llm_client

    def execute(self,question : str,plan: list[str]) -> str:
        '''根据计划，逐步执行并解决问题'''
        history = '' # 用于存储步骤和结果的字符串

        print('\n--- 正在执行计划 ---')

        for i,step in enumerate(plan):
            print(f"\n-> 正在执行步骤 {i + 1}/{len(plan)}: {step}")

            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question = question,
                plan = plan,
                history = history if history else '无',   # 如果是第一步，则历史为空
                current_step = step
            )

            messages = [{'role':'user','content':prompt}]

            response_text = self.llm_client.think(messages=messages) or ''

            # 更新历史记录，为下一步做准备
            history += f'步骤{i+1} : {step}\n结果:{response_text}\n\n'

            print(f"✅ 步骤 {i + 1} 已完成，结果: {response_text}")
        # 循环结束后，最后一步的响应就是最终答案
        final_answer = response_text
        return final_answer
