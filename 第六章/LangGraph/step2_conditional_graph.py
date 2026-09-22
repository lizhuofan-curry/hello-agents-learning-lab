# 这一次改动把之前固定死了的流程改成了：
# 下一步去哪，不再提前固定，而是根据当前 State 决定
# 这就要用到 LangGraph 中特别重要的 add_conditional_edges()
from typing import TypedDict
from langgraph.graph import StateGraph,START,END

# 1.定义 State
class MyState(TypedDict):
    number : int
    result : str

# 2. 普通节点
def check_node(state:MyState):
    print('进入 check 节点')
    # 这里的 check_node 负责执行节点，而 route_number 负责决定下一条 Edge
    return {}

def big_node(state:MyState):
    print('进入 big_node')
    return {'result': "这个数字大于 10"}

def small_node(state:MyState):
    print('进入 small_node')
    return {'result' : '这个数字小于或等于 10'}

# 3.路由函数,它的任务是决定路线
def route_number(state:MyState):
    print("正在判断下一步去哪...")
    if state['number'] > 10:
        return "big"
    return 'small'

# 4.创建图
workflow = StateGraph(MyState)

# 5.添加节点
workflow.add_node('check',check_node)
workflow.add_node('big_node',big_node)
workflow.add_node('small_node',small_node)

# 6.普通边
workflow.add_edge(START,'check')

# 7.条件边
workflow.add_conditional_edges(
    # 表示执行完哪个 Node 后开始判断
    'check',
    # 表示 谁负责判断下一步去哪
    route_number,
    # 这就是路由结果与真实节点之间的对应关系
    {
        'big':'big_node',
        'small':'small_node',
    }
)

# 8.到达 END
workflow.add_edge('big_node',END)
workflow.add_edge('small_node',END)

# 9. 编译
app = workflow.compile()

# 10.执行
result = app.invoke({
    'number':20,
    'result': ''
})

print(result)
