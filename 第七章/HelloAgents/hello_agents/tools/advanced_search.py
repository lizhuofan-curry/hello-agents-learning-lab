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

    def _search_with_tavily(
            self,
            query:str
    ) -> str:
        '''使用 Tavily 搜索'''
        response = self.tavily_client.search(
            query=query,
            max_results=3
        )

        result = ""

        if response.get('answer'):
            result +=  f"AI直接答案：{response['answer']}\n\n"

        result += '相关结果：\n'

        for i,item in enumerate(response.get('results',[])[:3],1):
            result += (f"[{i}] {item.get('title','')}\n")
            result +=f"   {item.get('content','')[:150]}...\n"

        return result

    def _search_with_serpapi(
            self,
            query:str
    ) -> str:
        '''使用 SerpApi 搜索'''
        import serpapi

        search = serpapi.GoogleSearch(
            {
                'q': query,
                'api_key': os.getenv('SERPAPI_API_KEY'),
                'num': 3,
            }
        )
        results = search.get_dict()

        result = "Google 搜索结果: \n"

        if "organic_results" in results:
            for i,item in enumerate(results['organic_results'][:3],1):
                result += (f"[{i}]"f"{item.get('title','')}\n")

                result += (f"   "
                           f"{item.get('snippet','')}\n"
                )

                result+=(
                    f"   来源："
                    f"{item.get('link','')}\n\n"
                )
            return result

    # 统一接口 / 屏蔽后端差异
    def search(
            self,
            query:str
    ) -> str:
        '''执行智能多源搜索'''
        # 1. 检查查询是否为空
        if not query.strip():
            return '错误，搜索查询不能为空'

        # 2. 检查是否存在可用搜索源
        if not self.search_sources:
            return (
                '没有可用的搜索源'
                '请检查 API Key 和相关依赖'
            )
        print(f'开始智能搜索: {query}')

        # 3. 按顺序尝试搜索源
        # 这是 fallback 最核心的控制流
        for source in self.search_sources:
            try:
                # Tavily
                if source == 'tavily':
                    print("正在尝试 Tavily...")
                    result = self._search_with_tavily(query)

                    if result:
                        return ("Tavily 搜索结果：\n\n" + result)
                # SerpApi
                elif source == 'serpapi':
                    print("正在尝试 SerpApi...")
                    result = self._search_with_serpapi(query)
                    if result:
                        return ("SerpApi 搜索结果：\n\n" + result)

            except Exception as e:
                print(f'{source} 搜索失败：{e}')
                print("尝试下一个搜索源....")
                # 如果没有 fallback 思维，程序可能直接结束，导致整个搜索失败
                # 这就是所谓的 服务降级(fallback)
                continue
        # 4. 所有搜索源都失败
        return (
            '所有搜索源都失败了，'
            '请检查网络，API Key 或服务状态'
        )

