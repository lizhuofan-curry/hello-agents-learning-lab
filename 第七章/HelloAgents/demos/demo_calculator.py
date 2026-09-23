from hello_agents.tools.calculator import CalculatorTool

calculator = CalculatorTool()

test_cases = [
    "2 + 3",
    "10 - 4",
    "5 * 6",
    "15 / 3",
    "2 + 3 * 4",
    "sqrt(16)",
]

print(calculator)

for expression in test_cases:
    result = calculator.execute(expression)

    print(f"{expression} = {result}")

