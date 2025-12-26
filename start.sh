#!/bin/bash

# 1. 强制清理锁文件 (防止重复启动失败)
rm -f /tmp/.X99-lock

# 2. 后台启动所有桌面组件，全部使用 & 分离进程
# 这里的顺序不影响启动，因为它们都是异步的
Xvfb :99 -screen 0 1280x720x24 -ac &
export DISPLAY=:99

# 启动 D-Bus (不使用 eval 阻塞，直接后台运行)
dbus-daemon --session --address=unix:path=/tmp/dbus-session --fork --print-address > /tmp/dbus-addr &
export DBUS_SESSION_BUS_ADDRESS="unix:path=/tmp/dbus-session"

# 启动窗口管理器
openbox &

echo "正在等待桌面环境初始化 (sleep 5s)..."
sleep 5
echo "环境准备就绪，正在启动 Python 程序。"

# 3. 立即启动 Python (前台运行，作为容器主进程)
echo "所有环境已异步启动，正在进入 Python..."
exec python3 testip.py
