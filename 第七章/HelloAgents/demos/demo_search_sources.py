from dotenv import load_dotenv

from hello_agents.tools.advanced_search import MyAdvancedSearchTool

load_dotenv()

search_tool = MyAdvancedSearchTool()

print('\n============= 搜索状态 =================')
print(search_tool.search_sources)

print("\n========== Hybrid 搜索测试 ==========")
result = search_tool.search("人工智能最新发展")

print(result)