#!/bin/bash

# 1. 启动 Xvfb (虚拟显示)
# :99 表示显示端口，-ac 允许所有客户端连接
Xvfb :99 -screen 0 1280x720x24 -ac &
export DISPLAY=:99

# 2. 等待 Xvfb 准备就绪
sleep 2

# 3. 启动 Openbox (窗口管理器)
# 很多有界面的程序需要它来处理窗口层级和焦点
openbox-session &

# 4. 启动 x11vnc (可选：方便你远程查看桌面)
# 如果不需要监控界面，可以删掉这行
# x11vnc -display :99 -forever -nopw -rfbport 5900 &

# 5. 运行你的 Python 程序
# 使用 exec 确保 Python 成为容器的主进程（PID 1），方便接收退出信号
exec python3 main.py
