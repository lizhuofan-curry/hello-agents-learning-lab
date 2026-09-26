from hello_agents.tools.registry import ToolRegistry
from hello_agents.tools.calculator import CalculatorTool
def say_hello(name:str) -> str:
    '''向指定的人打招呼'''
    return f"你好，{name}"

registry = ToolRegistry()
calculator = CalculatorTool()

registry.register_function(
    name='say_hello',
    description='向指定的人打招呼',
    func=say_hello,
)
registry.register_tool(calculator)

print("\n========== 执行普通函数工具 ==========")

result = registry.execute_tool('say_hello','小明')
print(result)

print('\n============== 工具描述 ===============')
description = registry.get_tools_description()
print(description)