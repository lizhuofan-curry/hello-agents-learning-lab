# 为了凸显 Plan-and-Solve 范式在结构化推理上的优势
# 将不使用工具的方式，而是通过提示词的设计，完成一个推理任务
# 规划阶段的目标是让大语言模型接收原始问题，并输出一个清晰的，分步骤的行动计划
# 这个计划必须是结构化的，以便我们的代码可以轻松解析并逐一执行
import ast

PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划,```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

# 将这个提示词逻辑封装成一个 Planner 类，这个类也是我们的规划器
class Planner:
    def __init__(self,llm_client) :
        self.llm_client = llm_client

    def plan(self,question:str) -> list[str]:
        '''根据用户问题生成一个行动计划'''
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)

        # 为了生成计划，我们构建一个简单的消息列表
        messages = [{'role':'user','content':prompt}]

        print('--- 正在生成计划 ---')
        # 使用流式输出来获取完整计划
        response_text = self.llm_client.think(messages = messages) or ''

        print(f"✅ 计划已生成:\n{response_text}")

        # 解析 LLM 输出的列表字符串
        try:
            # 找到 '''python 和 ''' 之间的内容
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            # 使用 ast.literal_eval 来安全地执行字符串，将其转换为Python列表
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan,list) else []
        except (ValueError,SyntaxError,IndexError) as e:
            print(f"❌ 解析计划时出错: {e}")
            print(f"原始响应: {response_text}")
            return []
        except Exception as e:
            print(f"❌ 解析计划时发生未知错误: {e}")
            return []

