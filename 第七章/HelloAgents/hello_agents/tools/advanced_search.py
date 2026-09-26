import os

class MyAdvancedSearchTool:
    '''自定义多源搜索工具'''
    def __init__(self):
        self.name = 'my_advanced_search'
        self.description = (
            "智能搜索工具，支持多个搜索源"
            "自动选择可用的搜索服务"
        )
        # 这个列表专门记录：当前真正能工作的搜索源
        self.search_sources = []

        self._setup_search_sources()

    def _setup_search_sources(self):
        '''检测当前有哪些搜索源可用'''

        # 检查 Tavily
        # 去环境变量中寻找，然后加载
        if os.getenv('TAVILY_API_KEY'):
            try:
                # 有 key 不代表 Python 库就一定安装了
                from tavily import TavilyClient

                self.tavily_client = TavilyClient(
                    api_key=os.getenv('TAVILY_API_KEY')
                )
                # 记录状态
                self.search_sources.append('tavily')
                print('Tavily 搜索源已启用')

            except ImportError:
                print('Tavily API Key 已配置'
                      '但 Tavily 库没有安装')

        # 检查 SerpApi
        if os.getenv('SERPAPI_API_KEY'):
            try:
                import serpapi
                self.search_sources.append('serpapi')
                print('SerpApi 搜索源已启用')

            except ImportError:
                print(
                    'SerpApi API Key 已配置'
                    '但 SerpApi 库没有安装'
                )

        # 最终状态
        if self.search_sources:
            print('当前可用搜索源：',self.search_sources)
        else:
            print('当前没有可用的搜索源')


