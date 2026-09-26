from dotenv import load_dotenv

from hello_agents.tools.advanced_search import create_advanced_search_registry
load_dotenv()

registry = create_advanced_search_registry()

print("\n========== 工具描述 ==========")

print(registry.get_tools_description())

print('\n============== Registry 搜索测试 ================')
result = registry.execute_tool('advanced_search','Python 编程语言的历史')
print(result)