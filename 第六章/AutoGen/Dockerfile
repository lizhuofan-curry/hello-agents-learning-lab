# 拿我们之前下载的Python 镜像当成底座
FROM python:3.12-slim

# 在这个 Docker 环境里面装 Streamlit 和 requests
RUN pip install --no-cache-dir streamlit requests

# 以后容器主要在 /app 目录工作
WORKDIR /app