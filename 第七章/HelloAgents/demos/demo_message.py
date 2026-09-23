from hello_agents.core.message import Message

message1 = Message(
    role='user',
    content='你好'
)
message2 = Message(
    role='assistant',
    content="你好,有什么可以帮助你？"
)
print(message1)
print(message2)
print(message1.to_dict())
print(message2.to_dict())
