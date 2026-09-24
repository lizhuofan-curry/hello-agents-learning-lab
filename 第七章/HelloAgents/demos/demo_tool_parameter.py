from hello_agents.tools.base import ToolParameter

parameter = ToolParameter(
    name = "expression",
    type = 'string',
    description="需要计算数学表达式",
    required=True
)

print(parameter)

print("\n参数名称:")
print(parameter.name)

print("\n参数类型:")
print(parameter.type)

print("\n参数说明:")
print(parameter.description)

print("\n是否必填:")
print(parameter.required)

print('\n默认值:')
print(parameter.default)