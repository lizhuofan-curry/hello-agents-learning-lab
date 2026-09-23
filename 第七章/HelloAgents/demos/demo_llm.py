from dotenv import load_dotenv

from hello_agents.core.llm import HelloAgentsLLM

load_dotenv()

llm = HelloAgentsLLM()

messages = [
    {
        "role":"user",
        "content":"请用解释什么是智能体框架"
    }
]
print("====== 普通调用 ======")
response = llm.invoke(messages)

print(response)

print("\n======== 流式输出 ========")

for chunk in llm.think(messages):
    # end='' 意思是打印完不要自动换行
    # flush = True 意思是不要把输出囤在缓存区，马上显式出来
    print(chunk, end='',flush=True)
print()