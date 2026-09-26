from dotenv import load_dotenv

from hello_agents.tools.advanced_search import MyAdvancedSearchTool

load_dotenv()

search_tool = MyAdvancedSearchTool()

print('\n============= 搜索状态 =================')
print(search_tool.search_sources)

print("\n============= Tavily 搜索测试 =================")
result = search_tool.search('Python 编程语言的历史')
print(result)

print("\n============= SerpApi 搜索测试 =================")

result = search_tool._search_with_serpapi("Python 编程语言的历史")

print(result)