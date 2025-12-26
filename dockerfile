FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    openbox \
    xvfb \
    x11vnc \
    python3 \
    python3-pip \
    git \
    curl \
    wget \
    sudo \
    && apt clean

# 安装 Playwright 及 Chromium
RUN pip3 install playwright && \
    playwright install --with-deps chromium

# 创建工作目录
WORKDIR /app

# 将你的代码复制进镜像
COPY . /app

# 默认启动脚本
CMD ["python3", "main.py"]
