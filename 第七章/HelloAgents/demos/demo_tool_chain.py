from hello_agents.tools.registry import ToolRegistry
from hello_agents.tools.tool_chain import ToolChain

def clean_text(
        text:str
) -> str :
    ''' 去掉文本两遍空格'''
    return text.strip()

def count_text(
        text:str
) -> str:
    '''统计文本长度'''
    return str(len(text))

registry = ToolRegistry()
registry.register_function(
    name='clean_text',
    description='清除文本两遍的空格',
    func = clean_text
)
registry.register_function(
    name = 'count_text',
    description='统计文本字符数量',
    func = count_text
)

chain = ToolChain(
    name= 'clean_and_count',
    description='先清理文本，再统计字符数'
)

chain.add_step(
    tool_name='clean_text',
    input_template='{input}',
    output_key='clean_result'
)
chain.add_step(
    tool_name='count_text',
    input_template='{clean_result}',
    output_key='count_result'
)

result = chain.execute(
    registry=registry,
    initial_input='   hello_agent   '
)

print('\n=============== 最终输出结果 ==============')
print(result)
