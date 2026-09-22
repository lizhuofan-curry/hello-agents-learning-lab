'''
一个良好定义的工具应该包含以下三个核心要素：
1.名称 ：一个简洁、唯一的标识符，供智能体在 Action 中调用，例如 Search
2.描述： 一段清晰的自然语言描述，说明这个工具的用途。这是整个机制中最关键的部分
3.执行逻辑： 真正执行任务的函数或方法
'''

# 去环境变量中取 SERPAPI_API_KEY
# find_ditenv 找到 .env 文件来哪里，load_dotenv 找到后把里面的变量加载到程序环境里
import os
import ast
import operator
from dotenv import load_dotenv, find_dotenv
# 我们的第一个工具是 search 函数，它的作用是接收一个查询字符串，然后返回搜索结果
from serpapi import SerpApiClient
from typing import Dict,Any

# 自动寻找当前目录及父目录中的 .env
env_path = find_dotenv()
load_dotenv(env_path)

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPERATORS = {
    ast.UAdd : operator.pos,
    ast.USub : operator.neg,
}

def _evaluate(node):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("只允许数字")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)

        if op_type not in OPERATORS:
            raise ValueError("不支持该运算符")

        left = _evaluate(node.left)
        right = _evaluate(node.right)

        return OPERATORS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)

        if op_type not in UNARY_OPERATORS:
            raise ValueError("不支持该运算符")

        return UNARY_OPERATORS[op_type](
            _evaluate(node.operand)
        )

    raise ValueError("表达式中包含不允许的内容")

def calculate(expression : str) -> str:
    try:
        tree = ast.parse(expression, mode='eval')
        result = _evaluate(tree)
        return str(result)

    except Exception as e:
        return f'计算错误: {e}'

def search(query: str) -> str:
    '''
    一个基于 SerpApi的实战网页搜索引擎工具
     它会智能地解析搜索结果，优先返回直接答案或知识图谱信息
    '''
    print(f'🔍 正在执行 [SerpApi] 网页搜索: {query}')
    # 工具失败不应该轻易导致整个 Agent 死掉
    try:
        api_key = os.getenv('SERPAPI_API_KEY')
        if not api_key:
            return "错误:SERPAPI_API_KEY 未在 .env 文件中配置。"

        # 这就相当于一个 python 字典
        params = {
            'engine':'google',
            'q':query,
            'api_key':api_key,
            'gl':'cn', # 国家代码
            'hl':'zh-cn',# 语言代码，简体英文
        }
        client = SerpApiClient(params)  # 根据这些参数准备一个 SerpApi 客户端
        results = client.get_dict()     # 这相当于一个很大的字典，SerpApi 帮我们把 Google 页面变成了程序容易读取的结构化数据

        '''
        在下列代码中，首先会检查是否存在 answer_box (Google的答案摘要框)
        或 kownledge_graph (知识图谱) 等信息
        如果存在，就直接返回这些最精确的答案
        如果不存在，才会退而求其次，返回前三个常规搜索结果的摘要
        这种智能解析能为LLM提供质量更高的信息输入
        '''
        # 智能解析 ： 优先寻找最直接的答案
        if 'answer_box_list' in results:
            return '\n'.join(results['answer_box_list'])
        if 'answer_box' in results and 'answer' in results['answer_box']:
            return results['answer_box']['answer']
        # 如果 Google 已经给了一个比较完整的实体简介，就直接把简介返回
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                # 如果没有 title就给我一个空字符串
                f"[{i + 1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            # 此时还是列表 List ,但是希望最后返回字符串，所以用join
            return "\n\n".join(snippets)
        return f"对不起，没有找到关于 '{query}' 的信息。"
    except Exception as e:
        return f"搜索时发生错误: {e}"

# 构建通用的工具执行器
# 当智能体需要使用多种工具时 (例如，除了搜索，还可能需要计算，查询数据库等)
# 我们需要一个统一的管理器来注册和调度这些工具
# 因此我们创建一个 ToolExecutor 类
class ToolExecutor:
    '''
    一个工具执行器，负责管理和执行工具，根据名字找到正确函数
    '''
    def __init__(self):
        self.tools:Dict[str,Dict[str,Any]] = {}

    def registerTool(self,name:str,description:str,func:callable):
        '''向工具箱中注册一个新工具'''
        if name in self.tools:
            print(f"警告：工具'{name}'已存在，将被覆盖")
        self.tools[name] = {'description':description,'func':func}
        print(f"工具'{name}'已注册")

    def getTool(self,name:str) -> callable:
        '''根据名称获取一个工具的执行函数'''
        # 注意这里得到的是函数，而不是搜索结果
        return self.tools.get(name,{}).get('func')

    def getAvailableTools(self) -> str:
        '''获取所有可用的格式化描述字符串'''
        return '\n'.join([
            f"- {name}:{info['description']}"
            for name,info in self.tools.items()
        ])

# 测试
# 将 search 工具注册到 ToolExecutor 中，并模拟一次调用
# ---- 工具初始化与使用示例 ------
if __name__ == '__main__':
    # 1. 初始化工具执行器
    toolExecutor = ToolExecutor()

    # 2.注册我们的实战搜索工具
    # 这个是给大模型看的，让大模型判断
    search_description = '一个网页搜索引擎。当你需要回答关于时事，事实以及在你的知识库中找不到的信息时，应使用此工具'
    toolExecutor.registerTool('Search',search_description,search)
    toolExecutor.registerTool(
        "Calculator",
        "用于精确计算数学表达式，例如 (123 + 456) * 789 / 12。",
        calculate
    )

    # 3.打印可用工具
    print('\n --- 可用的工具 ---')
    print(toolExecutor.getAvailableTools())

    # 4.智能体的 Action 调用，这次我们问一个实时性的问题
   # print("\n--- 执行 Action : Search['英伟达最新的GPU型号是什么'] ---")
    tool_name = 'Calculator'
    tool_input = '(123 + 456) * 789 / 12'

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print('--- 观察 (Observation) ---')
        print(observation)
    else:
        print(f"错误:未找到名为 '{tool_name}' 的工具。")