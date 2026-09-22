# 更好的进行异步处理
import asyncio
# Python 自带的文件路径工具
from pathlib import Path

# AutoGen提供的“取消按钮”，如果某个任务执行时间过长，可以通过它通知执行器来取消
from autogen_core import CancellationToken
# CodeBlock作用是:把一段代码包装起来，同时告诉 AutoGen 这是什么语言
from autogen_core.code_executor import CodeBlock
# 负责在 Docker 容器里面执行代码
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor

'''验证 AutoGen 能不能把一段Python代码丢进Docker容器里执行，然后把执行结果拿回来'''

# 本质上就是 Docker Executor的体检程序
# 开始定义一个异步主函数
async def main():
    # 创建工作目录
    work_dir = Path("../docker_workspace") # 表示创建一个路径对象，路径叫docker_workspace
    # 创建文件夹
    work_dir.mkdir(exist_ok=True)

    # 就是创建Docker的执行器，相当于创建一个执行python代码的小隔离房间
    async with DockerCommandLineCodeExecutor(
        image="python:3.12-slim",   # 之前执行了 docker pull python:3.12-slim ,所以现在本地有镜像
        work_dir=work_dir,  # 工作文件放在这个目录
        timeout=30,
    ) as executor:

        # await 意思是先等 Docker 执行完，再继续往下走
        # 所以保存的是 Docker 最后执行的结果
        result = await executor.execute_code_blocks(
            # 意思是我要执行一个Python 代码块
            # 注意现在是为了验证 不是 Windows 执行，而是 Docker 执行
            code_blocks=[
                CodeBlock(
                    language="python",
                    code='print("Hello from AutoGen Docker!")'
                )
            ],
            cancellation_token=CancellationToken(),
        )

        # 上方的result不是字符串，而是一个结果对象
        print("退出码：", result.exit_code)
        print("执行输出：")
        print(result.output)


if __name__ == "__main__":
    asyncio.run(main())