from hello_agents.core.config import Config

from dotenv import load_dotenv

load_dotenv()

config = Config.from_env()

print(config.temperature)
print(config.max_tokens)
print(config.debug)
print(config.max_history_length)