import time
import random
import ctypes
import sys, os
from typing import Optional
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PC.hid_device import HIDInput

user32 = ctypes.WinDLL("user32", use_last_error=True)

VK_NUMLOCK = 0x90
VK_CAPITAL = 0x14


def find_rock_window() -> Optional[int]:
    windows = []
    def callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        if "洛克王国：世界" in buf.value:
            windows.append(hwnd)
        return True
    WNDENUMPROC = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return windows[0] if windows else None


def get_client_rect(hwnd: int):
    rect = (ctypes.c_long * 4)()
    user32.GetClientRect(hwnd, rect)
    return rect[2], rect[3]


def key_toggled(vk: int) -> bool:
    return (user32.GetKeyState(vk) & 1) != 0


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def main():
    log("洛克王国丢球 - HID版  (CapsLock=暂停  NumLock关=退出  Ctrl+C=中断)")

    hwnd = find_rock_window()
    if not hwnd:
        log("未找到游戏窗口")
        return
    w, h = get_client_rect(hwnd)
    log(f"窗口句柄={hwnd}  客户区={w}x{h}")

    dev = HIDInput()
    count = rate_count = 0
    start = rate_start = time.monotonic()
    paused = False

    try:
        while True:
            if not key_toggled(VK_NUMLOCK):
                elapsed = time.monotonic() - start
                log(f"NumLock关 共{count}球  平均{count/elapsed:.1f}球/秒")
                break

            if key_toggled(VK_CAPITAL):
                if not paused:
                    log("暂停")
                    paused = True
                pause_start = time.monotonic()
                while key_toggled(VK_CAPITAL):
                    time.sleep(0.1)
                paused = False
                pause_sec = time.monotonic() - pause_start
                start += pause_sec
                rate_start += pause_sec
                log(f"恢复  暂停{pause_sec:.1f}秒")
                continue

            dev.mouse.click("left", hold_ms=random.randint(165, 185))
            time.sleep(random.uniform(0.09, 0.11))
            dev.mouse.click("right", hold_ms=random.randint(15, 35))

            count += 1
            rate_count += 1
            now = time.monotonic()
            if now - rate_start >= 2.0:
                log(f"#{count}  {rate_count/(now-rate_start):.1f}球/秒")
                rate_count = 0
                rate_start = now
    except KeyboardInterrupt:
        elapsed = time.monotonic() - start
        log(f"中断 共{count}球  平均{count/elapsed:.1f}球/秒" if count else "中断")


if __name__ == "__main__":
    main()
