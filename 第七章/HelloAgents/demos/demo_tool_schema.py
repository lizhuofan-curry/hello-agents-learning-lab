import json

from hello_agents.tools.calculator import CalculatorTool

calculator = CalculatorTool()

print("=========== 工具参数 ============")

parameters = calculator.get_parameters()

for parameter in parameters:
    print(parameter)


print("\n============ OpenAI Schema ==========")
schema = calculator.to_openai_schema()

# 这里是为了输出美观，indent = 2 表示漂亮的缩进两格
# ensure_ascii = False 保证中文直接显示成：需要计算的数学表达式
print(json.dumps(schema,ensure_ascii=False,indent=2))