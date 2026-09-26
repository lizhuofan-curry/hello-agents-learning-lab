from hello_agents.tools.registry import (
    ToolRegistry
)

from hello_agents.tools.tool_chain import (
    ToolChain,
    ToolChainManager
)


def clean_text(
    text: str
) -> str:
    return text.strip()


def count_text(
    text: str
) -> str:
    return str(
        len(text)
    )


# 1. 创建工具注册表
registry = ToolRegistry()


registry.register_function(
    name="clean_text",
    description="清除文本两边空格",
    func=clean_text
)


registry.register_function(
    name="count_text",
    description="统计字符数量",
    func=count_text
)


# 2. 创建一条工具链
chain = ToolChain(
    name="clean_and_count",
    description="先清理文本，再统计长度"
)


chain.add_step(
    tool_name="clean_text",
    input_template="{input}",
    output_key="clean_result"
)


chain.add_step(
    tool_name="count_text",
    input_template="{clean_result}",
    output_key="count_result"
)


# 3. 创建 Manager
manager = ToolChainManager(
    registry
)


# 4. 注册工具链
manager.register_chain(
    chain
)


print(
    "\n========== 当前工具链 =========="
)

print(
    manager.list_chains()
)


# 5. 通过 Manager 执行
result = manager.execute_chain(
    chain_name="clean_and_count",
    input_data="   hello_agent   "
)


print(
    "\n========== 最终结果 =========="
)

print(result)