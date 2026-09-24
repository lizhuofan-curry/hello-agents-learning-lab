# 用来读取环境变量
import os
# 例如： model:optional[str] = None ,意思是model不一定为空，而是有两种类型 str 和 None
# Iterator[str] 表示这个东西会连续产生多个 str
from typing import Optional,Iterator

from openai import OpenAI

class HelloAgentsLLM:

    def __init__(
            self,
            model: Optional[str] = None,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            temperature: float = 0.7,
            timeout : int = 60
    ):
        # 表示存在就用，不存在就查看环境变量中是否有，即显式传参 > 环境变量
        self.model = model or os.environ.get("LLM_MODEL_ID")
        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        self.base_url = base_url or os.environ.get("LLM_BASE_URL")

        self.temperature = temperature
        self.timeout = timeout

        # 为框架设计里很重要的 Fail Fast 尽早失败
        if not self.model:
            raise ValueError("没有找到模型名称")
        if not self.api_key:
            raise ValueError("没有找到 API Key")
        if not self.base_url:
            raise ValueError("没有找到 Base URL")

        # 真正创建 OpenAI SDK 客户端
        # _client 表示这是内部属性，外面最好别直接碰
        # 也就是说 _client 技术上能访问，但我们希望用户使用 llm.invoke
        # 而不是使用 llm.client.chat.completions.create
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

    '''
    dict[str,str] 表示：
    {
    "role": "user",
    "content": "你好"
    } 
    意思是 key 是 str , value 也是 str
    而 list[dict[str,str]] 表示：
    [
    {
        "role": "system",
        "content": "你是AI助手"
    },
    {
        "role": "user",
        "content": "你好"
    }
    ]
    这其实就是对话历史，后面写 Message 类，就是准备进一步把这里抽象掉
    '''
    # 完整返回
    def invoke(self,messages:list[dict[str,str]]) -> str:
        # 真正发请求的是这里，调用回来以后 response 不是一个字符串，而是一个很大的响应对象
        # 所以真正的回复文本在 response.choice[0].message.content
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return response.choices[0].message.content or ""
    # 流式返回
    def think(
            self,
            messages:list[dict[str,str]]
    ) -> Iterator[str]:
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            stream=True,
        )
        # 流式返回的是很大 chunk
        # 所以这里的循环是一块一块处理
        for chunk in stream:
            # 这里由之前的 message.content 变成了 delta.content
            # delta 经常表示 增量/变化量
            content = chunk.choices[0].delta.content
            if content:
                # yield 和 return 完全不一样
                # return 返回结果，然后函数结束
                # yield 它不是一次调用返回三个结果，而是变成一个生成器 Generator
                # 所以 yield 不是结束函数，而是“暂时停止”
                yield content
