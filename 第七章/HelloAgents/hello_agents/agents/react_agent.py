"""ReAct Agent"""

# re 是 Python 自带的 Regular Expression：正则表达式模块
import re

from hello_agents.core.message import Message
from hello_agents.core.agent import Agent
from hello_agents.tools.registry import ToolRegistry

REACT_PROMPT = """
你是一个具备推理和行动能力的 AI 助手。

## 可用工具

{tools}

## 工作方式

请分析用户的问题，并严格按照下面的格式输出：

Thought: 你的分析
Action: 你的行动

Action 只能使用下面两种格式之一：

工具调用：
工具名[工具输入]

任务完成：
Finish[最终答案]

如果问题需要数学计算，请优先使用 calculator 工具，
不要直接心算得到最终答案。

## 用户问题

{question}

## 当前执行历史

{history}

现在请输出本轮的 Thought 和 Action：
"""
class ReActAgent(Agent):
    """ReAct 智能体"""

    def __init__(
            self,
            name:str,
            llm,
            tool_registry:ToolRegistry,
            system_prompt:str|None = None,
            config=None,
            max_steps:int = 5,
    ):
        super().__init__(
            name = name,
            llm = llm,
            system_prompt=system_prompt,
            config = config
        )
        self.tool_registry = tool_registry

        # 第一次出现一个新的历史，和之前的 self._history 不是同一个东西
        # self._history 保存的是 用户和 Agent 的对话历史
        # self.current_history 保存的是 这一次任务内部的 ReAct 执行过程
        # 其实也就是 Memory 和 State 的区别
        # _history 更偏长期一点的记忆，current_history 更偏当前 ReAct任务的执行状态
        self.current_history : list[str] =[]
        self.max_steps = max_steps

    def _parse_output(
            self,
            response_text:str
    ) -> tuple[str|None,str|None]:
        '''解析模型输出中的 Thought 和 Action'''
        # 在 response_text 中寻找符合这种模型的内容
        # \s* 表示后面可用跟任意数量的空白字符
        # (.*) 表示把后面的所有内容抓出来
        thought_match = re.search(
            r"Thought:\s*(.*)",
            response_text
        )

        action_match = re.search(
            r"Action:\s*(.*)",
            response_text
        )
        # group(1) 拿正则表达式里面的 (.*)也叫捕获组
        thought = thought_match.group(1).strip() if thought_match else None

        action = action_match.group(1).strip() if action_match else None

        return thought,action

    # 继续拆 action
    def _parse_action(
            self,
            action:str
    ) -> tuple[str|None,str|None]:
        '''解析工具名称和工具输入'''
        # 这里的 fullmatch 比 search 更严格，可用理解成：
        # search : 这一大段里面有没有符合要求的
        # fullmatch : 你整段是不是都符合要求
        match = re.fullmatch(
            # ([a-zA-Z_]\w*) 负责匹配 calculator 也就是工具名
            r"([a-zA-Z_]\w*)\[(.*)\]",
            action
        )

        if not match:
            return None,None

        tool_name = match.group(1)
        tool_input = match.group(2).strip()

        return tool_name,tool_input

    # 继续解析 Finish
    def _parse_finish(
            self,
            action:str
    ) -> str|None:
        """解析 Finish 中的最终答案"""
        match = re.fullmatch(r"Finish\[(.*)]",action)

        if not match:
            return None
        return match.group(1).strip()

    def run(self,input_text:str) -> str:
        """运行完整的 ReAct 循环"""

        # 每个任务都需要重新开始
        self.current_history = []

        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n=========== 第{current_step}步 ================")

            # 1. 获取工具描述
            tools_description = self.tool_registry.get_tools_description()

            # 2. 拼接当前 ReAct 执行历史
            history_text = "\n".join(self.current_history)

            # 3. 构造 Prompt
            prompt = REACT_PROMPT.format(
                tools = tools_description,
                question = input_text,
                history = history_text
            )

            # 4. 调用 LLM
            message = [
                {
                    'role':'user',
                    'content':prompt,
                }
            ]

            response = self.llm.invoke(message)

            print('\n模型输出 :')
            print(response)

            # 5.解析 Thought 和 Action
            thought,action = self._parse_output(response)

            print("\nThought:")
            print(thought)

            print("\nAction:")
            print(action)

            # 如果连 Action 都没解析出来
            if action is None:
                self.current_history.append(
                    "Observation : 模型没有按照要求输出 Action"
                )
                continue

            # 6. 判断是否 Finish
            if action.startswith("Finish"):
                final_answer = self._parse_finish(action)

                if final_answer is None:
                    final_answer = "无法解析最终答案"

                # 保存真正的用户对话历史
                self.add_message(
                    Message(
                        role = 'user',
                        content=input_text
                    )
                )
                self.add_message(
                    Message(
                        role = 'assistant',
                        content=final_answer,
                    )
                )

                return final_answer

            # 7. 解析工具调用
            tool_name,tool_input = self._parse_action(action)
            if tool_name is None:
                self.current_history.append(f"Action : {action}")
                self.current_history.append(f"Observation : 工具调用格式错误")
                continue

            print('\nTool Name:')
            print(tool_name)

            print('\nTool Input:')
            print(tool_input)

            # 8.真正执行工具
            observation = self.tool_registry.execute_tool(tool_name, tool_input)

            print('\nObservation :')
            print(observation)

            # 9. 保存本轮 ReAct 历史
            if thought :
                self.current_history.append(f"Thought : {thought}")

            self.current_history.append(f"Action : {action}")
            self.current_history.append(f"Observation : {observation}")

        # 10. 超过最大步数
        final_answer = "抱歉，我无法在限定步数内完成这个任务"

        self.add_message(
            Message(
                role = 'user',
                content=input_text
            )
        )
        self.add_message(
            Message(
                role = 'assistant',
                content=final_answer
            )
        )
        return final_answer