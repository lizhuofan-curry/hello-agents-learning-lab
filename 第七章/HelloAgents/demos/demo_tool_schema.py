import json

from hello_agents.tools.calculator import CalculatorTool

calculator = CalculatorTool()

print("=========== 工具参数 ============")

parameters = calculator.get_parameters()

for parameter in parameters:
    print(parameter)


print("\n============ OpenAI Schema ==========")
# 这个 Schema 不是计算器本身，而是 “计算器的说明书”
# 它只是拿去告诉 LLM: 我这里有一个工具，叫 calculator，它能计算数学，而且你调用它的时候，需要给我一个名为 expression 的字符串参数
schema = calculator.to_openai_schema()

# 这里是为了输出美观，indent = 2 表示漂亮的缩进两格
# ensure_ascii = False 保证中文直接显示成：需要计算的数学表达式
print(json.dumps(schema,ensure_ascii=False,indent=2))