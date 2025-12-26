#!/bin/bash

# 1. 启动 Xvfb
rm -f /tmp/.X99-lock
Xvfb :99 -screen 0 1280x720x24 -ac +extension GLX +render -noreset &

# 等待桌面就绪
until xset -q -display :99 > /dev/null 2>&1; do
    sleep 0.5
done

export DISPLAY=:99

# 2. 核心修复：启动 D-Bus 临时会话并导出环境变量
# dbus-launch 会启动一个 dbus-daemon 并返回相关的环境变量
eval $(dbus-launch --sh-syntax)

# 3. 启动窗口管理器
openbox &

# 4. 运行 Python 程序
# 此时环境变量中已经有了 DBUS_SESSION_BUS_ADDRESS
echo "D-Bus 地址: $DBUS_SESSION_BUS_ADDRESS"
exec python3 main.py
