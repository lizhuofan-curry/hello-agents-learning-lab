from dotenv import load_dotenv

from hello_agents.tools.advanced_search import MyAdvancedSearchTool

load_dotenv()

class TestSearchTool(MyAdvancedSearchTool):
    '''专门用于测试 fallback'''
    # 进行方法重写
    def _search_with_tavily(
            self,
            query:str
    ) -> str:
        raise RuntimeError('模拟 Tavily 服务故障')

search_tool = TestSearchTool()

print("========== Fallback 测试 ==========")
result = search_tool.search("Python 编程语言的历史")

print('\n============ 最终结果 ==================')
print(result)