'''计算器工具'''

import ast
import math
import operator

from hello_agents.tools.base import BaseTool,ToolParameter

class CalculatorTool(BaseTool):
    '''安全的数学计算工具'''

    def __init__(self):
        # 这里super可以理解为 CalculatorTool的父类，也就是BaseTool
        # 这也是继承的一个重要用法：子类使用父类已经写好的初始化逻辑
        super().__init__(
            name = "calculator",
            description="数学计算工具，支持 +，-，*，/ 和 sqrt"
        )
    # 这才是计算器自己的能力
    def execute(self,input_data: str) -> str:
        if not input_data.strip():
            return "错误，计算表达式不能为空"

        try:
            # 为了保证安全，这里先把数学表达式解析成语法树，再只允许我们明确支持的节点
            node = ast.parse(input_data, mode="eval")
            result = self._eval_node(node.body)

            return str(result)

        except Exception as e:
            return f"计算失败：{e}"

    # Python 会优先使用子类自己的方法
    # 也就是 CalculatorTool.run() 覆盖了 BaseTool.run()
    # 这也叫做 方法重写
    def run(
            self,
            parameters :dict
    ) -> str:
        """新版接口 ： 使用参数字典执行计算"""
        print("进入 CalculatorTool.run()")
        if 'expression' not in parameters:
            return "计算失败：缺少参数 expression"
        expression = parameters['expression']

        return self.execute(str(expression))

    def get_parameters(self) -> list[ToolParameter]:
        """返回计算器需要的参数"""
        return [
            ToolParameter(
                name = 'expression',
                type = 'string',
                description='需要计算的数学表达式',
                required=True
            )
        ]

    # _eval_node 是递归运算
    def _eval_node(self,node):
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
        }

        if isinstance(node,ast.Constant):
            return node.value

        if isinstance(node,ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)

            op = operators.get(type(node.op))

            if op is None:
                raise ValueError("不支持这个运算符")
            return op(left, right)

        if isinstance(node,ast.Call):
            if(
                isinstance(node.func,ast.Name) and
                node.func.id == "sqrt"
            ):
                value = self._eval_node(node.args[0])
                return math.sqrt(value)

        raise ValueError("不支持的表达式")
