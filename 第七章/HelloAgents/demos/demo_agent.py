from dotenv import load_dotenv

from hello_agents.core.agent import Agent
from hello_agents.core.message import Message
from hello_agents.core.llm import HelloAgentsLLM

load_dotenv()

class EchoAgent(Agent):
    def run(self,input_text:str) -> str:
        response = f"你刚才说的是 : {input_text}"

        self.add_message(
            Message(
                role="user",
                content=input_text
            )
        )

        self.add_message(
            Message(
                role='assistant',
                content=response
            )
        )
        return response

llm = HelloAgentsLLM()

agent = EchoAgent(
    name = "Echo",
    llm = llm,
)

result = agent.run("你好")

print('Agent 回答:')
print(result)

print("\n历史记录:")

for message in agent.get_history():
    print(message)