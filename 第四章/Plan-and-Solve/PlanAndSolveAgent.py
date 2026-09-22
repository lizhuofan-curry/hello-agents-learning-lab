from llm_client import HelloAgentsLLM
from Plan import Planner
from Executor import Executor


# 现在已经分别构建了负责规划的 Planner 和负责执行的 Executor
# 最后一步是将这两个组件整合到一个统一的智能体 PlanAndSolveAgent中
# 并赋予它解决问题的完整能力

class PlanAndSolveAgent:
    def __init__(self,llm_client):
        '''初始化智能体，同时创建规划器和执行器实例'''
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client)

    def run(self,question : str):
        '''
        运行智能体的完整流程：先规划，后执行
        '''
        print(f"\n--- 开始处理问题 ---\n问题: {question}")

        # 1.调用规划器生成计划
        plan = self.planner.plan(question)

        # 检查计划是否生成成功
        if not plan:
            print("\n--- 任务终止 --- \n无法生成有效的行动计划。")
            return

        # 2.调用执行器执行计划
        final_answer = self.executor.execute(question,plan)
        print(f"\n--- 任务完成 ---\n最终答案: {final_answer}")

# --- 5. 主函数入口 ---
if __name__ == '__main__':
    try:
        llm_client = HelloAgentsLLM()
        agent = PlanAndSolveAgent(llm_client)
        question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"
        agent.run(question)
    except ValueError as e:
        print(e)