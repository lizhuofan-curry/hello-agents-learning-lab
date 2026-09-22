# 现在将所有独立组件，LLM客户端和工具执行器组装起来，构建一个完整的 ReAct 智能体
# 通过一个 ReActAgent 类来封装其核心逻辑

# 提供脑子
from 第四章.ReAct.Hello_Agent import HelloAgentsLLM
# 提供工具箱子
from React_v0 import ToolExecutor
# 提供工具
from React_v0 import search
import re


# 1. 系统提示词设计
# 提示词是整个 ReAct机制的基石，它将动态地插入可用工具，用户问题以及中间步骤的交互历史
# ReAct 提示词模板，故意留了三个洞 {tools},{question},{history}等运行时在往里面塞东西
# Python知道有哪些函数 不等于 LLM知道有哪些工具
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下:
{tools}

请严格按照以下格式进行回应:

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一:
- `{{tool_name}}[{{tool_input}}]`:调用一个可用工具。
- `Finish[最终答案]`:当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在Action:字段后使用 Finish[最终答案] 来输出最终答案。

现在，请开始解决以下问题:
Question: {question}
History: {history}
"""

# ReActAgent 的核心是一个循环，它不断地“格式化提示词” -> 调用LLM -> 执行动作 -> 整合结果
# 直到任务完成或者达到最大步数限制

class ReActAgent:
    def __init__(self,llm_clint:HelloAgentsLLM,tool_executor:ToolExecutor,max_steps : int = 5):
        # 给 Agent 装了四样东西
        self.llm_clint = llm_clint  # 大模型客户端
        self.tool_executor = tool_executor  # 工具执行器
        self.max_steps = max_steps  # 最多思考几轮
        self.history = []   # 行动历史
    '''
    run 方法是智能体的入口,它的 while循环构成了 ReAct范式的主体
    max_steps 参数则是一个重要的安全阀，防止智能体陷入无限循环而耗尽资源
    '''
    def run(self,question : str):
        ''' 运行ReAct智能体来回答一个问题 '''
        self.history = []   # 每次运行时重置历史记录，否则就串台了
        current_step = 0    # 注意这是没回答一个新问题时重置历史记录，同一个问题的不同步还是有历史记录存在的
        while current_step < self.max_steps :
            current_step += 1
            print(f'--- 第{current_step}步 ---')

            # 1.格式化提示词(先构造 Prompt)
            tool_desc = self.tool_executor.getAvailableTools()
            history_str = '\n'.join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools = tool_desc,
                question=question,
                history = history_str,
            )

            # 2.调用 LLM 进行思考
            messages = [{'role':'user','content':prompt}]
            response_text = self.llm_clint.think(messages = messages)

            if not response_text:
                print('错误:LLM未能返回有效响应')
                break

            # 3. 解析 LLM 的输出
            # 这里的 Thought，Action不是 Python 自动生成的
            # 是 LLM 看了 Prompt 以后，按照你的要求自己写出来的
            thought,action = self._parse_output(response_text)
            if thought:
                print(f'🤔思考:{thought}')

            if not action:
                print('警告：未能解析出有效的Action，流程终止。')
                break

            # 4. 执行Action
            if action.startswith('Finish'):
                # 如果是 Finish指令，提取最终答案并结束
                final_answer = re.match(r"Finish\[(.*)\]", action,re.DOTALL).group(1)
                print(f"🎉 最终答案: {final_answer}")
                return final_answer

            tool_name,tool_input = self._parse_action(action)
            if not tool_name or not tool_input :
                '''... 处理无效 Action格式 ...'''
                continue

            print(f"🎬 行动: {tool_name}[{tool_input}]")
            tool_function = self.tool_executor.getTool(tool_name)
            if not tool_function:
                observation = f"错误:未找到名为'{tool_name}'的工具"
            else:
                observation = tool_function(tool_input) # 调用真实工具

            print(f"👀 观察: {observation}")

            '''
            最后一步，也就是形成闭环的关键
            是将 Action本身和工具执行后的 Observation 添加回历史记录中，为下一轮循环提供新的上下文
            通过将 observation 追加到 self.history 
            智能体在下一轮生成提示词时，就能看到上一步行动的结果，并据此进行新一轮的思考和规划
            '''
            # 将本轮的 Action 和 Observation 添加到历史记录中
            self.history.append(f'Action:{action}')
            self.history.append(f'Observation:{observation}')

        # 循环结束
        print('已达到最大步数，流程终止')
        return None


    # 负责从LLM的完整响应中分离出 Thought 和 Action 两个主要部分
    def _parse_output(self,text:str):
        '''解析 LLM 的输出，提取 Thought 和 Action'''

        # Thought : 匹配到 Action : 或文本末尾
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # Action : 匹配到文本末尾
        # 找 Action，然后把它后面的内容抓到字符串结束
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        # 如果匹配到了，就取括号里面的内容，再用strip()去掉前后空格
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    # 负责进一步解析 Action 字符串，例如从Search[华为最新手机] 中提取出工具名 Search 和工具，输入华为最新手机
    def _parse_action(self, action_text: str):
        """解析Action字符串，提取工具名称和输入。"""
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
        return None, None


if __name__ == '__main__':

    # 1.创建 LLM 客户端
    llm_clint = HelloAgentsLLM()

    #2.创建工具执行器
    tool_executor = ToolExecutor()

    # 3.注册 Search 工具
    search_description = (
        "一个网页搜索引擎。"
        "当你需要回答关于时事、事实以及知识库中找不到的信息时，"
        "应该使用这个工具。"
    )

    tool_executor.registerTool(
        "Search",
        search_description,
        search
    )

    # 4.创建 ReAct Agent
    agent = ReActAgent(
        llm_clint = llm_clint,
        tool_executor = tool_executor,
        max_steps = 10
    )

    # 5.给 Agent 一个需要搜索才能回答的问题
    question = "帮我了解目前最新的DeepSeek模型，它是什么时候发布的，有什么主要能力？"

    print("\n==============================")
    print("用户问题：", question)
    print("==============================\n")

    # 6. 启动 Agent
    final_answer = agent.run(question)

    print("\n==============================")
    print("Agent 最终返回：")
    print(final_answer)
    print("==============================")


