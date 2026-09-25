from hello_agents.tools.calculator import CalculatorTool
calculator = CalculatorTool()

print("================ 旧接口 =================")
result1 = calculator.execute("23 * 17 + 5")
print(result1)

print('\n============== 新接口 ==================')
result2 = calculator.run({"expression": "23 * 17 + 5"})
print(result2)