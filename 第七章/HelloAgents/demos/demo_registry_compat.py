from hello_agents.tools.calculator import CalculatorTool
from hello_agents.tools.registry import ToolRegistry

registry = ToolRegistry()

calculator = CalculatorTool()

registry.register_tool(calculator)

print("============ 旧版调用 ================")
result1 = registry.execute_tool("calculator","23 * 17 + 5")
print(result1)

print('\n============= 新版调用 =================')
result2 = registry.execute_tool(
    'calculator',
    {
        'expression' : '23 * 17 + 5'
    }
)
print(result2)

print('\n============== 不存在的工具 ===============')
result3 = registry.execute_tool(
    'banana',
    {
        'expression' : '23 * 17 + 5'
    }
)
print(result3)