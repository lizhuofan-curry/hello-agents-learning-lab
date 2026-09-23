"""Plan-and-Solve Agent"""

import ast

from hello_agents.core.agent import Agent

DEFAULT_PROMPTS ="""
你是一个AI规划专家。

你的任务是把用户提出的问题分解成多个简单、可执行的步骤。

问题：
{question}

请严格按照 Python 列表格式输出计划：

["步骤1", "步骤2", "步骤3"]

不要输出列表以外的任何内容。
"""
# 自然语言计划 -> 结构化计划 -> 程序循环执行
class PlanAndSolveAgent(Agent):
    """规划并执行智能体"""

    def _make_plan(
            self,
            question:str,
    ) -> list[str]:
        prompt = DEFAULT_PROMPTS.format(question=question)
        messages = [
            {
                'role' : 'user',
                'content' : prompt,
            }
        ]

        # 模型看起来输出 ["计算周二", "计算周三", "计算总数"]
        # 但本质上还是 str ,也就是 response = '["计算周二", "计算周三", "计算总数"]'
        # 所以现在还不能把它当作 list 来处理
        response = self.llm.invoke(messages)

        print("\n========= Planner 原始输出 =============")
        print(response)
        # ast.literal_eval 只允许解析比较安全的 Python 字面量，不会随便执行函数调用或者系统命令
        plan = ast.literal_eval(response.strip())
        return plan
    def run(self,input_text:str) -> str:
        ''' V1 只负责生成计划'''
        plan = self._make_plan(input_text)

        plan_text = "\n".join(
            f"{i}:{step}"
            for i,step in enumerate(plan,1)
        )
        return plan_text


