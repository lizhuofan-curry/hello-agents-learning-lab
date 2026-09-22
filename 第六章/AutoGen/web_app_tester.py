import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

'''
现在web_app_tester.py 的身份变了，它是：我是一个工具箱，等别人调用我 
所以后面可以直接变成：
report = test_streamlit_app("output.py") 
 '''


CONTAINER_NAME = "autogen-streamlit-test"

HOST_PORT = 8502
CONTAINER_PORT = 8501

IMAGE_NAME = "autogen-streamlit:latest"


def find_docker():
    """
    查找 docker.exe。
    """

    docker_path = shutil.which("docker")

    if docker_path:
        return docker_path

    fallback = (
        r"C:\Users\Lenovo\AppData\Local"
        r"\Programs\DockerDesktop\resources\bin\docker.exe"
    )

    if Path(fallback).exists():
        return fallback

    raise FileNotFoundError("没有找到 docker.exe")


def test_streamlit_app(app_path: str) -> str:
    """
    在 Docker 中启动指定的 Streamlit 应用，
    然后访问 Streamlit health endpoint。

    参数：
        app_path:
            要测试的 Python 文件路径。
            例如：
            "output.py"

    返回：
        测试报告字符串。
    """

    # ---------------------------------------------------------
    # 1. 找到项目目录
    # ---------------------------------------------------------

    project_dir = Path(__file__).resolve().parent

    # ---------------------------------------------------------
    # 2. 找到要测试的应用
    # ---------------------------------------------------------

    app_file = Path(app_path)

    # 如果传入的是相对路径，例如 output.py
    if not app_file.is_absolute():
        app_file = project_dir / app_file

    app_file = app_file.resolve()

    # 文件不存在，直接测试失败
    if not app_file.exists():
        return (
            "WEB_APP_TEST_FAIL\n"
            f"找不到应用文件：{app_file}"
        )

    # ---------------------------------------------------------
    # 3. 确认这个文件位于项目目录内部
    # ---------------------------------------------------------

    try:
        relative_app_path = app_file.relative_to(project_dir)
    except ValueError:
        return (
            "WEB_APP_TEST_FAIL\n"
            "应用文件必须位于 AutoGen 项目目录中。"
        )

    # Windows:
    # output.py
    #
    # Docker:
    # /app/output.py

    docker_app_path = (
        "/app/"
        + relative_app_path.as_posix()
    )

    # ---------------------------------------------------------
    # 4. 找 Docker
    # ---------------------------------------------------------

    try:
        docker = find_docker()
    except Exception as e:
        return (
            "WEB_APP_TEST_FAIL\n"
            f"Docker 查找失败：{e}"
        )

    # ---------------------------------------------------------
    # 5. 清理可能残留的旧容器
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 6. 准备 docker run 命令
    # ---------------------------------------------------------

    command = [
        docker,
        "run",
        "-d",

        "--name",
        CONTAINER_NAME,

        "-p",
        f"{HOST_PORT}:{CONTAINER_PORT}",

        "-v",
        f"{project_dir}:/app",

        IMAGE_NAME,

        "streamlit",
        "run",
        docker_app_path,

        "--server.address=0.0.0.0",
        f"--server.port={CONTAINER_PORT}",
        "--server.headless=true",
    ]

    try:

        # -----------------------------------------------------
        # 7. 启动 Docker + Streamlit
        # -----------------------------------------------------

        start_result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )

        container_id = start_result.stdout.strip()

        health_url = (
            f"http://localhost:"
            f"{HOST_PORT}/_stcore/health"
        )

        # -----------------------------------------------------
        # 8. 最多等待 30 秒
        # -----------------------------------------------------

        for attempt in range(30):

            try:

                with urllib.request.urlopen(
                    health_url,
                    timeout=2,
                ) as response:

                    status_code = response.status

                    content = (
                        response.read()
                        .decode("utf-8")
                        .strip()
                    )

                    # -----------------------------------------
                    # Streamlit 成功启动
                    # -----------------------------------------

                    if status_code == 200:

                        return (
                            "WEB_APP_TEST_PASS\n"
                            f"Container ID: {container_id}\n"
                            f"HTTP Status: {status_code}\n"
                            f"Health Response: {content}"
                        )

            except Exception:
                time.sleep(1)

        # -----------------------------------------------------
        # 9. 超时，读取 Docker 日志
        # -----------------------------------------------------

        logs = subprocess.run(
            [
                docker,
                "logs",
                CONTAINER_NAME,
            ],
            capture_output=True,
            text=True,
        )

        return (
            "WEB_APP_TEST_FAIL\n"
            "Streamlit 在 30 秒内没有通过健康检查。\n\n"
            "Docker stdout:\n"
            f"{logs.stdout}\n\n"
            "Docker stderr:\n"
            f"{logs.stderr}"
        )

    except Exception as e:

        # Docker 自己启动失败
        return (
            "WEB_APP_TEST_FAIL\n"
            f"Docker 启动失败：{e}"
        )

    finally:

        # -----------------------------------------------------
        # 10. 无论成功失败都删除容器
        # -----------------------------------------------------

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