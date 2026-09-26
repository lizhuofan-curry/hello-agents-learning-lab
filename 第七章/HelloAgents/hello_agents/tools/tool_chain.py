from typing import Any

from hello_agents.tools.registry import ToolRegistry

class ToolChain:
    '''多个工具按照固定顺序执行'''
    def __init__(
            self,
            name:str,
            description:str,
    ):
        self.name = name
        self.description = description
        # 现在 ToolChain 里面最重要的是 steps
        # 它用来保存第1步做什么,第2步做什么...
        self.steps : list[dict[str,Any]] = []

    def add_step(
            self,
            tool_name:str,
            input_template:str,
            output_key:str | None = None,
    ):
        """给工具链添加一个步骤"""
        self.steps.append(
            {
                'tool_name':tool_name,
                'input_template':input_template,
                'output_key':(
                    output_key
                    or f'step_{len(self.steps)}_result'
                )
            }
        )

    def execute(
            self,
            registry:ToolRegistry,
            initial_input:str,
            context:dict[str,Any]|None = None,
    ) -> str:
        '''按照顺序执行整条工具链'''
        context = context or {}
        # 程序真正运行时用来存数据的仓库
        context['input'] = initial_input
        print(f'开始执行工具链：{self.name}')
        # # 看一开始的 context
        # print(f'初始 context', context)

        for i,step in enumerate(self.steps,1):
            tool_name = step['tool_name']
            input_template = step['input_template']
            output_key = step['output_key']

            # 根据 context 替换模板变量
            try:
                tool_input = (
                    # 根据模板里的名字，到 context 中找真正的数据
                    input_template.format(**context)
                )
            except KeyError as e:
                return (
                    f'工具链执行失败：'
                    f'找不到模板变量 {e}'
                )
            print(
                f'步骤 {i}:'
                f'调用 {tool_name}'
            )

            # 执行工具
            result = registry.execute_tool(tool_name,tool_input)

            # 保存当前步骤结果
            # output_key 决定结果在 context 里面叫什么名字
            context[output_key] = result

            print(f'步骤 {i} 完成：{result}')
            # 看执行完这一轮后的 context
            # print('执行后的 context',context)

        # 返回最后一步结果
        final_key = self.steps[-1]['output_key']

        return context[final_key]

class ToolChainManager:
    '''工具链管理器'''
    def __init__(
            self,
            registry:ToolRegistry,
    ):
        self.registry = registry
        # Manager 用来保存所有工具链的字典
        self.chains : dict[str,ToolChain] = {}

    def register_chain(
            self,
            chain:ToolChain
    ):
        '''注册工具链'''
        self.chains[chain.name] = chain
        print(f"工具链 '{chain.name}' 已注册")

    def execute_chain(
            self,
            chain_name : str,
            input_data : str,
            context: dict[str,Any]|None = None,
    ) -> str:
        '''根据名字执行指定工具链'''
        if chain_name not in self.chains:
            return f"工具链 '{chain_name}' 不存在"

        chain = self.chains[chain_name]

        return chain.execute(
            registry=self.registry,
            initial_input=input_data,
            context=context,
        )

    def list_chains(self) -> list[str]:
        '''返回所有工具链名称'''
        return list(self.chains.keys())

