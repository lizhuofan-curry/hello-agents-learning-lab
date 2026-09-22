# 为了让代码结构更清晰，更易于复用
# 我们来定义一个专属的 LLM 客户端类
# 这个类将封装所有于模型交互的细节
import os
# OpenAI Python SDK 提供的客户端类
# 不一定真的在调用 OpenAI 官方模型，但是用的服务兼容 OpenAI API
from openai import OpenAI
from dotenv import load_dotenv
from typing import List,Dict

# 加载 .env 文件中的环境变量
load_dotenv()

# 定义 LLM 客户端类
class HelloAgentsLLM:
    '''
    为本书 ‘Hello Aegnts’ 定制的 LLM 客户端
    它用于调用任何兼容 OpenAI 接口的服务，并默认使用流式响应
    '''
    def __init__(self,model:str = None,apiKey:str =None,baseUrl:str = None,timeout:int = None):
        '''
        初始化客户端，优先使用传入参数，如果未提供，则从环境变量加载
        '''
        self.model = model or os.getenv('LLM_MODEL_ID')
        apiKey = apiKey or os.getenv('LLM_API_KEY')
        baseUrl = baseUrl or os.getenv('LLM_BASE_URL')
        timeout = timeout or int(os.getenv('LLM_TIMEOUT',60))

        if not all([self.model,apiKey,baseUrl]):
            raise ValueError('模型ID,API密钥和服务地址必须被提供或在.env文件中定义')
        # 客户端
        self.client = OpenAI(api_key=apiKey,base_url=baseUrl,timeout=timeout)

    # 调用模型
    # messages 是一个 List ,List 里面每一项是 Dict ,Dict 里面 key和 value 都是字符串
    def think(self,messages:List[Dict[str,str]],temperature:float = 0) -> str :
        '''
        调用大语言模型进行思考，并返回其响应
        '''
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,    # 流式输出
            )

            # 处理流式响应
            print("✅ 大语言模型响应成功:")
            collected_content = []
            for chunk in response:
                if not chunk.choices:
                    continue
                # 当前这个 chunk 里面模型刚刚生成的文字
                content = chunk.choices[0].delta.content or ""
                print(content,end='',flush=True) # end = '' 打完之后不要换行，flush = True ：立刻把输出刷新到终端
                collected_content.append(content)
            print()     # 在流式输出结束后换行
            return ''.join(collected_content)
        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None

# ------- 客户端使用示例 ---------
if __name__ == '__main__':
    try:
        llmClient = HelloAgentsLLM()

        exampleMessages = [
            {'role':'system','content':'You are a helpful assistant that writes Python code'},
            {'role':'user','content':'写一个快速排序算法'}
        ]
        print('--- 调用LLM ---')
        responseText = llmClient.think(exampleMessages)
        if responseText:
            print('\n\n --- 完整版模型响应 ---')
            print(responseText)

    except Exception as e:
        print(e)



