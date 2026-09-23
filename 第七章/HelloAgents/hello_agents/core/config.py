'''统一程序应该怎么运行'''
import os

from pydantic import BaseModel

# config 也集成 BaseModel ,也是让 Pydantic 帮我们创建对象 + 设置默认值 + 检查类型
class Config(BaseModel):
    """HelloAgents 的统一配置"""

    temperature:float = 0.7
    max_tokens: int | None = None
    debug:bool = False
    # 以后 Agent 会保存 _history 也就是会话历史，但是不能无限增长
    max_history_length: int = 100

    # 普通方法 首先要有对象然后才config.test()
    # 这里是类方法，可以直接 Config.from_env(),不需要提前创建对象
    @classmethod
    # cls 可以理解成 当前这个类本身
    # 例如 Config.from_env()调用的不是某个config而是 Config这个类
    # 所以 cls = Config 因此 return cls 就是 return Config
    # 所以这个函数的意思是 从环境变量读取配置，然后创建一个 Config 对象返回
    def from_env(cls):
        return cls(
            temperature = float(os.environ.get("TEMPERATURE", 0.7)),
            max_tokens = (int(os.getenv("MAX_TOKENS")) if os.getenv("MAX_TOKENS") else None),
            debug = (os.getenv("DEBUG","false").lower() == "true"),
        )