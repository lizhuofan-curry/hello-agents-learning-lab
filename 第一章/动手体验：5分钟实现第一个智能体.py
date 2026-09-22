AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具:
- `get_weather(city: str)`: 查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。

# 输出格式要求:
你的每次回复必须严格遵循以下格式，包含一对Thought和Action：

Thought: [你的思考过程和下一步计划]
Action: [你要执行的具体行动]

Action的格式必须是以下之一：
1. 调用工具：function_name(arg_name="arg_value")
2. 结束任务：Finish[最终答案]

# 重要提示:
- 每次只输出一对Thought-Action
- Action必须在同一行，不要换行
- 当收集到足够信息可以回答用户问题时，必须使用 Action: Finish[最终答案] 格式结束

请开始吧！
"""

# 工具1 : 查询真实天气
# 我们将使用免费的天气查询服务 wttr.in ，它能以 JSON 格式返回指定城市的天气数据：
import requests

def get_weather(city: str) -> str:
    '''
    通过调用 wttr.in API 查询真实的天气信息
    '''
    # API 端点，我们请求JSON格式的数据
    url = f'https://wttr.in/{city}?format=j1'

    try:
        # 发起网络请求
        response = requests.get(url,timeout = 15)
        # 检查响应状态码是否为200（成功）
        response.raise_for_status()
        # 解析返回的 JSON 数据
        data = response.json()

        # 提取当前天气状况
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']

        # 格式转化为自然语言返回
        return f'{city}当前天气：{weather_desc},气温{temp_c}摄氏度'

    except requests.exceptions.RequestException as e:
        # 处理网络错误
        return f'错误:查询天气时遇到网络问题 -{e}'
    except (KeyError, IndexError) as e:
        # 处理数据解析错误
        return f'错误:解析天气数据失败，可能是城市名称无效 -{e}'

# 工具 2 : 搜索并推荐旅游景点
# 定义一个新工具 get_attraction ,它会根据城市和天气状况，在互联网上搜索合适的景点
import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

def get_attraction(city: str, weather: str) -> str:
    '''
    根据城市和天气，使用Tavily Search API 搜索并返回优化后的景点推荐
    '''
    # 1.从环境变量中读取 API 密钥
    api_key = os.environ.get('TAVILY_API_KEY')
    if not api_key:
        return '错误：未配置 TAVILY_API_KEY 环境变量'

    # 2. 初始化 Tavily 客户端
    tavily = TavilyClient(api_key=api_key)

    # 3. 构造一个精确的查询
    query = f'‘{city}’在’{weather}‘天气下最值得去的旅游景点推荐及理由'

    try:
        # 4. 调用API,include_answer=True 会返回一个综合性的回答
        response = tavily.search(query=query,search_depth='basic',include_answer=True)

        # 5. Tavily 返回的结果已经非常干净可以直接使用
        # response['answer'] 是一个基于所有搜索结果的总结性问答
        if response.get('answer'):
            return response['answer']

        # 如果没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get('results',[]):
            formatted_results.append(f"- {result['title']}:{result['content']}")

        if not formatted_results:
            return '抱歉，没有找到相关的旅游景点推荐。'
        return '根据搜索，为你找到一下信息：\n ' + '\n'.join(formatted_results)
    except Exception as e:
        return f'错误：执行Tavily 搜索时出现问题 - {e}'

# 将所有工具函数放入一个字典，方便后续调用
available_tools = {
    'get_weather': get_weather,
    'get_attraction': get_attraction,
}

# 接入大语言模型
# 我们实现一个通用的客户端 OpenAICompatibleClient , 它可以连接到任何兼容 OpenAI 接口规范的LLM服务
from openai import OpenAI

class OpenAICompatibleClient:
    '''
    一个用于调用任何兼容OpenAI接口的LLM服务的客户端
    '''
    def __init__(self,model:str,api_key:str,base_url:str):
        self.model = model
        self.client = OpenAI(api_key=api_key,base_url=base_url)

    def generate(self,prompt:str,system_prompt:str) -> str:
        '''
        调用LLM API来生成响应
        '''
        print('正在调用大语言模型...')
        try:
            messages = [
                {'role': 'system','content':system_prompt},
                {'role':'user','content':prompt},
            ]
            response = self.client.chat.completions.create(
                model = self.model,
                messages = messages,
                stream=False
            )
            answer  = response.choices[0].message.content
            print('大语言模型响应成功。')
            return answer
        except Exception as e:
            print(f'调用LLM API 时发生错误: {e}')
            return '错误，调用语言模型服务时错误'


import re

#  --------- 1.配置LLM客户端 -------------
# 从项目根目录的 .env 读取配置，禁止把真实密钥写入代码。
API_KEY = os.getenv('LLM_API_KEY')
BASE_URL = os.getenv('LLM_BASE_URL')
MODEL_ID = os.getenv('LLM_MODEL_ID')

missing_env = [
    name
    for name, value in {
        'LLM_API_KEY': API_KEY,
        'LLM_BASE_URL': BASE_URL,
        'LLM_MODEL_ID': MODEL_ID,
        'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
    }.items()
    if not value
]
if missing_env:
    raise RuntimeError(f"缺少环境变量: {', '.join(missing_env)}，请参考 .env.example")

llm = OpenAICompatibleClient(model=MODEL_ID,api_key=API_KEY,base_url=BASE_URL)

# ---------- 2.初始化 ------------
user_prompt = '你好，请帮我查询一下今天长沙的天气，然后根据天气推荐一个合适的旅游景点'
prompt_history = [f'用户请求: {user_prompt}']

print(f'用户输入: {user_prompt}\n' + '='*40)

# ---------- 3.运行主循环 -----------
for i in range(5): # 设置最大循环次数
    print(f'--- 循环 {i+1} --- \n')

    # 3.1 构造Prompt
    full_prompt = '\n'.join(prompt_history)

    # 3.2 调用LLM进行思考
    llm_output = llm.generate(full_prompt,system_prompt=AGENT_SYSTEM_PROMPT)
    # 模型可能会输出多余的Thought-Action，需要截断
    match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
    if match:
        truncated = match.group(1).strip()
        if truncated != llm_output.strip():
            llm_output = truncated
            print("已截断多余的 Thought-Action 对")
    print(f"模型输出:\n{llm_output}\n")
    prompt_history.append(llm_output)

    # 3.3 解析并执行行动
    action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
    if not action_match:
        observation = "错误: 未能解析到 Action 字段。请确保你的回复严格遵循 'Thought: ... Action: ...' 的格式。"
        observation_str = f"Observation: {observation}"
        print(f"{observation_str}\n" + "=" * 40)
        prompt_history.append(observation_str)
        continue
    action_str = action_match.group(1).strip()

    if action_str.startswith("Finish"):
        # 最终答案可能包含多行内容，re.DOTALL 让 . 能匹配换行符。
        finish_match = re.match(r"Finish\[(.*)\]", action_str, re.DOTALL)
        if not finish_match:
            print("错误：最终答案格式不正确，应为 Finish[最终答案]")
            break

        final_answer = finish_match.group(1)
        print(f"任务完成，最终答案:\n{final_answer}")
        break

    tool_name = re.search(r"(\w+)\(", action_str).group(1)
    args_str = re.search(r"\((.*)\)", action_str).group(1)
    kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

    if tool_name in available_tools:
        observation = available_tools[tool_name](**kwargs)
    else:
        observation = f"错误:未定义的工具 '{tool_name}'"

    # 3.4. 记录观察结果
    observation_str = f"Observation: {observation}"
    print(f"{observation_str}\n" + "=" * 40)
    prompt_history.append(observation_str)
