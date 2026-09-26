from hello_agents.tools.my_calculator import create_calculator_registry

registry = create_calculator_registry()

test_cases = [
    "2 + 3",
    "10 - 4",
    "5 * 6",
    "15 / 3",
    "sqrt(16)",
]

for i,expression in enumerate(test_cases,1):
    print(f"测试{i}: {expression}")

    result = registry.execute_tool('my_calculator', expression)

    print(f'结果 : {result}\n')
