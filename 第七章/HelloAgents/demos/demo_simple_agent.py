from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.agents.simple_agent import SimpleAgent

load_dotenv()

llm = HelloAgentsLLM()

agent = SimpleAgent(
    name="学习助手",
    llm=llm,
    system_prompt="你是一个耐心的AI学习助手，回答尽量简洁"
)

print("======== 第一轮 ==========")

response1 = agent.run("我叫小明，请记住我的名字")

print(response1)

print("========= 第二轮 ==========")

response2 = agent.run("我叫什么名字？")

print(response2)

print("\n======== 对话历史 ===========")

for message in agent.get_history():
    print(message)