FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# 安装桌面环境 + Xvfb + Python
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

# 安装 Playwright
RUN pip3 install playwright && \
    playwright install --with-deps chromium

WORKDIR /app
COPY . /app

CMD ["xvfb-run", "--server-args=-screen 0 1280x720x24", "python3", "main.py"]
