# 这里主要用到 shutil.which("docker"),去当前系统的 PATH 环境变量中寻找 docker 命令到底在哪
import shutil
# 它允许 Python去启动另外一个外部程序
# 例如平时写 docker images ,python可以通过 subprocess.run()来替我执行
import subprocess
# 记录时间，因为 Docker容器启动了，不代表 Streamlit 服务器瞬间就启动好了
import time
# 它负责 Python 自动访问网页，如 urllib.request.urlopen()
import urllib.request
# 这个可以获得当前 Python 文件的位置
from pathlib import Path

'''
自动化测试 Streamlit 网页是否真的启动成功
'''

# Docker 容器名字
CONTAINER_NAME = "autogen-streamlit-health-test"

# 我们不用 8501，避免和你现在手动启动的 Streamlit 冲突
# 这里的 HOST 指 Windows主机，也就是说 Windows 使用 8502，但是 Docker 容器内部 Streamlit 使用 8501
HOST_PORT = 8502

'''
所以 Windows localhost : 8502
通过 Docker 端口映射到
Container 8501
因为此时我本机的Windows已经有一个手动的 Streamlit测试占用了 8501
'''
# Docker 容器内部 Streamlit 仍然监听 8501
CONTAINER_PORT = 8501


def find_docker():
    """
    找到 docker.exe。
    """

    docker_path = shutil.which("docker")

    if docker_path:
        return docker_path

    # 你的 Docker Desktop 实际安装位置
    fallback = (
        r"C:\Users\Lenovo\AppData\Local"
        r"\Programs\DockerDesktop\resources\bin\docker.exe"
    )

    if Path(fallback).exists():
        return fallback

    raise FileNotFoundError("没有找到 docker.exe")


def main():
    # =========================================================
    # 1. 找到项目根目录
    # =========================================================

    # 当前文件：
    # AutoGen/test/test_streamlit_health.py
    #
    # parent:
    # AutoGen/test
    #
    # parent.parent:
    # AutoGen
    project_dir = Path(__file__).resolve().parent.parent

    docker = find_docker()

    print("项目目录：", project_dir)
    print("Docker：", docker)

    # =========================================================
    # 2. 如果之前有同名容器，先删除
    # =========================================================

    # 相当于终端 : docker rm -f autogen-streamlit-health-test
    subprocess.run(
        [
            docker,
            "rm",
            "-f",
            CONTAINER_NAME,
        ],
        # 不要把这个命令的普通输出和错误输出打印到终端
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # =========================================================
    # 3. 启动 Docker + Streamlit
    # =========================================================

    command = [
        docker,
        "run",

        # 后台运行
        "-d",    # 代表 detached mode 后台运行，如果不加的话，Streamlit 会一直霸占终端，这样后面的健康检查根本无法进行

        # 这也就是 docker run 意思是 创建并启动一个容器
        # -----------------------------------------------------------------

        # 给容器起名字
        # 相当于 --name autogen-streamlit-health-test
        "--name",
        CONTAINER_NAME,

        # Windows 8502 -> Docker 8501
        # 意思是 -p 8502:8501 即 Windows 8502 -> Docker Container 8501
        # 所以 Python 后面访问 http://localhost:8502 实际上最终到了容器的 Streamlit 的 8501
        "-p",
        f"{HOST_PORT}:{CONTAINER_PORT}",

        # 把整个 AutoGen 项目挂载到容器 /app
        # 这叫做 Volume Mount 目录挂载
        # 例如 Windows 的 AutoGen 目录会映射到 Docker 的 /app，
        # 因此 AutoGen/test/streamlit_test.py 在容器中是
        # /app/test/streamlit_test.py。
        
        "-v",
        f"{project_dir}:/app",

        # 使用我们刚刚制作好的镜像
        "autogen-streamlit:latest",

        # 容器里面真正执行的命令
        # 实际上就是在容器里面执行 streamlit run /app/test/streamlit_test.py
        "streamlit",
        "run",
        "/app/test/streamlit_test.py",

        "--server.address=0.0.0.0",         # 告诉 Streamlit 不要只监听容器内部的localhost,而要监听容器所有网络接口，因为 Windows 还要通过 Docker 端口映射访问它
        f"--server.port={CONTAINER_PORT}",  # Streamlit 在容器内部 8501 监听
        "--server.headless=true",           # 不要试图在 Docker 容器里面打开浏览器 todo
    ]

    print("\n🐳 正在启动 Docker 容器...")

    try:
        # 可以理解成 Python 请执行这条外部命令，并等他结束
        result = subprocess.run(
            command,
            capture_output=True,    # 把 docker 命令输出抓回来，别直接仍在终端
            text=True,              # 把返回结果当作普通字符串处理，否则可能得到 bytes
            check=True,             # 如果 Docker 命令成功 exit code = 0 ,如果失败 exit code != 0 ,Python直接报异常，所以不会假装启动成功
        )
        # 运行 docker run -d... Docker 成功后会输出 9bccb25ab970... 也就是容器ID
        container_id = result.stdout.strip()

        print("✅ Docker 容器已启动")
        print("Container ID：", container_id)

        # =====================================================
        # 4. 自动检查 Streamlit health endpoint
        # =====================================================

        # 这里用的是 HOST_PORT ,因为我们是从 Windows 访问，然后经过端口映射到 Container 8501
        health_url = (
            f"http://localhost:{HOST_PORT}/_stcore/health"
        )

        print("\n🌐 正在检查：", health_url)

        # 最多等待 30 秒
        for attempt in range(30):

            try:
                # 正式发送 HTTP 请求
                # 相当于 Python 请访问这个 URL ,最多等 2 秒
                with urllib.request.urlopen(
                    health_url,
                    timeout=2,
                ) as response:

                    # 获得 HTTP 状态码 ，实际结果为 200 = OK , 所以 Web Server 正常
                    status_code = response.status
                    # 读取返回内容
                    content = (
                        response.read()     # 可能是 b'ok' 前面 b 表示 bytes
                        .decode("utf-8")    # 把 bytes 转成字符串 ‘ok’
                        .strip()            # 去掉前后空格和换行
                    )

                    print("\n==============================")
                    print("✅ Streamlit 健康检查成功")
                    print("==============================")

                    print("HTTP 状态码：", status_code)
                    print("返回内容：", content)

                    if status_code == 200:
                        print("\n🎉 WEB_APP_TEST_PASS")
                        return

            except Exception:
                print(
                    f"等待 Streamlit 启动..."
                    f" {attempt + 1}/30"
                )

                time.sleep(1)

        # =====================================================
        # 5. 30 秒还没成功
        # =====================================================

        print("\n❌ Streamlit 启动失败或健康检查超时")

        logs = subprocess.run(
            [
                docker,
                "logs",
                CONTAINER_NAME,
            ],
            capture_output=True,
            text=True,
        )

        print("\nDocker 日志：")
        print(logs.stdout)
        print(logs.stderr)

        print("\nWEB_APP_TEST_FAIL")

    # 无论前面成功，失败，报错，甚至 return,这里都必须执行
    finally:

        # =====================================================
        # 6. 无论成功还是失败，都清理 Docker 容器
        # =====================================================

        print("\n🧹 正在清理 Docker 容器...")

        # 相当于 docker rm -f autogen-streamlit-health-test
        # 这也就是测试程序一个很重要的思想 : 测试结束后恢复现场
        subprocess.run(
            [
                docker,
                "rm",
                "-f",
                CONTAINER_NAME,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        print("✅ Docker 容器已清理")


if __name__ == "__main__":
    main()
