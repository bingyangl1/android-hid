"""基础用法示例"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PC.hid_device import HIDInput

# 自动选最快传输 (ADB forward > TCP > SSH)
dev = HIDInput()
print(f"Transport: {dev.transport_name}")

# 鼠标点击
dev.mouse.click("left", 175)      # 左键，按住 175ms
dev.mouse.click("right", 40)      # 右键
dev.mouse.click("x1", 40)         # 侧键

# 鼠标移动
dev.mouse.move(100, -50)           # 向右100 向上50

# 键盘按键
dev.keyboard.tap("LSHIFT", 35)     # Shift 按 35ms
dev.keyboard.tap("F5")             # F5
dev.keyboard.tap("a")              # 字母 A

# 原始命令
dev.cmd("mclick:left:175")
dev.cmd("ktap:a:40")

# Ping 测试
print(dev.cmd("ping"))             # → pong
