# 不是 LangGragh 的内容，来自于 python
# 作用为 描述一个字典应该有哪些键，每个键应该是什么类型
# 因为 LangGraph 最核心的东西叫做 State 状态，我们程序运行的过程中，总得有东西在节点之间传来传去
# 所以后面规定 MyState , 意思就是 我的 LangGraph 状态里面，有一个叫 Number的变量，它是整数
from typing import TypedDict

from langgraph.graph import StateGraph,START,END

# 定义状态
class MyState(TypedDict):
    number : int

# 第一个节点
# 现在输入的是整个 state 即 {‘number’:5}
# 所以后面用 state['number'] 得到 5，于是这个节点返回 {'number':6} 更新了 number = 6
# LangGraph 的 Node 本质上就是一个 Python 函数 ： 作用为 拿到 State -> 进行处理 -> 返回 State 的更新内容
def add_one(state:MyState):
    print('进入 add_one')
    return {'number' : state['number']+1}

# 第二个节点
def double(state:MyState):
    print('进入 double')
    return {'number' : state['number'] * 2}

# 这是整个 LangGraph 真正开始的地方
# 意思是创建一张图，这张图运行过程中使用 MyState 保存状态
workflow = StateGraph(MyState)

# 添加节点
# 第一个是节点名字，为字符串
# 第二个是 Python 函数
# 所以这个意思是 创建一个名叫 “add_one” 的 Node,这个Node执行 add_one()函数
workflow.add_node('add_one',add_one)
workflow.add_node('double',double)

# 连接节点，这里主要是规定运行顺序
workflow.add_edge(START,'add_one')
workflow.add_edge('add_one','double')
workflow.add_edge('double',END)

# 注意，前面的workflow更接近图的设计稿，但它还不是最终运行对象
# 于是 compile()把设计好的图变成可以执行的 LangGraph 应用
app = workflow.compile()

# 执行，这里 “number”:5 就是初始 State
# app.invoke 意思就是用这个初始的State运行整张图
result = app.invoke({'number':5})

# 查看最终结果
print(result)