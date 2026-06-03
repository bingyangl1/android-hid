"""键盘多键同时按 + 指定按键 release 示例"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PC.hid_device import HIDInput

dev = HIDInput("adb", show_latency=True)

# 1. 单键 tap（按下→延迟→松开）
dev.keyboard.tap("a", 50)

# 2. 修饰键组合：Shift+A
dev.keyboard.press("LSHIFT")
dev.keyboard.press("a")
# 此时 Shift 和 A 同时按住
import time; time.sleep(0.1)
dev.keyboard.release("a")       # 只松开 A，Shift 还按着
dev.keyboard.release("LSHIFT")  # 松开 Shift

# 3. Ctrl+C
dev.keyboard.press("LCTRL")
dev.keyboard.press("c")
time.sleep(0.05)
dev.keyboard.release("c")
dev.keyboard.release("LCTRL")

# 4. 全松（兜底）
dev.keyboard.release()

print(dev.latency_str())
