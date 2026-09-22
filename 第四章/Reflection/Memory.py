# 在我们已经实现的 ReAct 和 Plan-and-Solve范式中，智能体一旦完成了任务，其工作流程便告结束
# 然而他们生成的初始答案，无论是行动轨迹还是最终结果，都可能存在谬误或有待改进之处
# Reflection机制的核心思想，正式为智能体引入一种事后的自我校正循环
# 使其能像人类一样，审视自己的工作，发现不足，并进行迭代优化

# Reflection 的核心在于迭代，而迭代的前提是能够记住之前的尝试
# 因此一个短期记忆模块是实现该范式的必需品
# 这个记忆模块将负责存储每一次”执行-反思“循环的完整轨迹

# 这几个东西都是 类型提示 其中 Optional 等价于 str| None
from typing import List,Dict,Any,Optional

class Memory:
    '''
    一个简单的短期记忆模块，用于存储智能体的行动与反思轨迹
    '''
    def __init__(self):
        '''初始化一个空列表来存储所有记录'''
        self.records : List[Dict[str,Any]] = []

    # 意思是写入记忆
    '''
    有两种 type 
    第一种是 execution 表示 : Agent 做出来的效果
    第二种是 reflection 表示 : 对上一轮执行结果的评价或反思
    这就是 Reflection 的循环骨架
    '''
    def add_records(self,record_type:str,content:str):
        '''
        向记忆中添加一条新纪录
        参数:
        - record_type (str): 记录的类型 ('execution 或 'reflection')
        - content (str): 记录的具体内容 (例如，生成的代码或反思的反馈)
        '''
        record = {'type':record_type,'content':content}
        self.records.append(record)
        print(f"📝 记忆已更新，新增一条 '{record_type}' 记录。")

    # trajectory 翻译过来就是 轨迹
    # 这里指 Agent 到目前为止整个“执行 -> 反思 -> 执行 -> 反思”的历史轨迹
    # get_trajectory 没有修改 Memory
    # 只是读取已有记忆，重新整理格式再返回一个字符串
    # 这个字符串以后最重要的用途就是 塞进 LLM 的 Prompt
    def get_trajectory(self) -> str:
        '''
        将所有记忆记录格式化为一个连贯的字符串文本，用于构建提示词
        '''
        trajectory_parts = []
        for record in self.records:
            if record['type'] == 'execution':
                trajectory_parts.append(f"--- 上一轮尝试 (代码) ---\n{record['content']}")
            elif record['type'] == 'reflection':
                trajectory_parts.append(f"--- 评审员反馈 ---\n{record['content']}")

        return "\n\n".join(trajectory_parts)

    # 这个函数的目标非常明确：找到最近一次 execution
    # 这里用reverse把列表翻转，便于寻找最近一次
    def get_last_execution(self) -> Optional[str]:
        '''
        获取最近一次的执行结果 (例如，最新生成的代码)
        如果不存在，则返回 None
        '''
        for record in reversed(self.records):
            if record['type'] == 'execution':
                return record['content']
        return None
