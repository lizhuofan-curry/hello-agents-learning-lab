from hello_agents.tools.calculator import CalculatorTool
from hello_agents.tools.registry import ToolRegistry

# 1. 创建工具注册表
registry = ToolRegistry()

# 2.创建计算器
calculator = CalculatorTool()

# 3. 注册计算器
registry.register_tool(calculator)

print("\n======= 已注册工具 =========")
print(registry.list_tools())

print("\n======== 工具描述 =========")
print(registry.get_tools_description())

print("\n========= 执行工具 ============")
result = registry.execute_tool('calculator','2 + 3 * 4')
print(result)

print('\n========= 执行不存在的工具 ===========')

result = registry.execute_tool('banana','hello')
print(result)