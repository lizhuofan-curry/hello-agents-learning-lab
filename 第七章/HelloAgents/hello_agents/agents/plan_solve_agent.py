"""Plan-and-Solve Agent"""

import ast

from hello_agents.core.agent import Agent

DEFAULT_PLANNER_PROMPT = """
你是一个AI规划专家。

你的任务是把用户提出的问题分解成多个简单、可执行的步骤。

你只负责制定计划，不要执行计算，
不要提前给出中间结果或最终答案。

问题：
{question}

请严格按照 Python 列表格式输出计划：

["步骤1", "步骤2", "步骤3"]

不要输出列表以外的任何内容。
"""

DEFAULT_EXECUTOR_PROMPT = """
你是一位AI执行专家。

你的任务是严格按照给定计划，
一次只执行当前步骤。

原始问题：
{question}

完整计划：
{plan}

已经完成的步骤和结果：
{history}

当前需要执行的步骤：
{current_step}

请只完成当前步骤。
不要提前执行后续步骤。

请直接输出当前步骤的结果。
"""
# 自然语言计划 -> 结构化计划 -> 程序循环执行
class PlanAndSolveAgent(Agent):
    """规划并执行智能体"""

    def _make_plan(
            self,
            question:str,
    ) -> list[str]:
        prompt = DEFAULT_PLANNER_PROMPT.format(question=question)
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

    def _execute_step(
            self,
            question:str,
            plan:list[str],
            history:list[str],
            current_step:str,
    ) -> str:
        '''执行计划中的一个步骤'''

        history_text = "\n".join(history) if history else "暂无"

        prompt = DEFAULT_EXECUTOR_PROMPT.format(
            question=question,
            plan=plan,
            history = history_text,
            current_step = current_step,
        )

        message = [
            {
                'role' : 'user',
                'content' : prompt,
            }
        ]

        result = self.llm.invoke(message)

        return result

    def run(self,input_text:str) -> str:
        ''' PLan-and-Solve V2 : 规划并逐步执行'''

        # 1.先生成计划
        plan = self._make_plan(input_text)

        print("\n========== 最终计划 ==========")

        for i,step in enumerate(plan,1):
            print(f"步骤{1}: {step}")

        # 保存执行历史
        execution_history : list[str] = []

        final_result = ''

        # 2. 一个步骤一个步骤执行
        for i,step in enumerate(plan,1):
            print(f"\n============= 执行步骤{i} ============")
            print("当前步骤：")
            print(step)

            result = self._execute_step(
                question=input_text,
                plan=plan,
                history=execution_history,
                current_step=step,
            )

            print("\n执行结果：")
            print(result)

            # 保存本步骤的执行结果
            execution_history.append(
                f'步骤 {i}: {step}\n'
                f'结果 {result}'
            )

            final_result = result
        return final_result


