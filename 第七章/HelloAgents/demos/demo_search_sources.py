from dotenv import load_dotenv

from hello_agents.tools.advanced_search import MyAdvancedSearchTool

load_dotenv()

search_tool = MyAdvancedSearchTool()

print('\n============= 搜索状态 =================')
print(search_tool.search_sources)