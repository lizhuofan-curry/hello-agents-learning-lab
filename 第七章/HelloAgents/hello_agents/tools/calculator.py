'''计算器工具'''

import ast
import math
import operator

from hello_agents.tools.base import BaseTool

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
