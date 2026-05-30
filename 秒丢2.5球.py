#!/usr/bin/env python3
# 后台键鼠统一模拟 - 洛克王国丢球脚本（使用左Shift + 状态监听 + 完整键位）
import datetime
import ctypes
import time
import random
from ctypes import wintypes
import sys
from functools import wraps
from typing import Callable, Any

from hid_device import HIDMouse, HIDKeyboard, HIDInput
# 初始化键鼠对象
dev = HIDInput()
# ==================== Windows API 初始化 ====================
user32 = ctypes.WinDLL('user32', use_last_error=True)
try:
    user32.SetProcessDPIAware()
except:
    pass

# ==================== 常量定义 ====================
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP   = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP   = 0x0208
WM_MOUSEMOVE   = 0x0200
WM_ACTIVATE    = 0x0006
WA_ACTIVE      = 1
MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002
MK_MBUTTON = 0x0004

WM_KEYDOWN = 0x0100
WM_KEYUP   = 0x0101

# 虚拟键码
VK_LSHIFT     = 0xA0
VK_RSHIFT     = 0xA1
VK_LCONTROL   = 0xA2
VK_RCONTROL   = 0xA3
VK_LMENU      = 0xA4   # 左Alt
VK_RMENU      = 0xA5   # 右Alt
VK_LWIN       = 0x5B
VK_RWIN       = 0x5C
VK_SPACE      = 0x20
VK_ENTER      = 0x0D
VK_TAB        = 0x09
VK_CAPITAL    = 0x14   # CapsLock
VK_NUMLOCK    = 0x90   # NumLock
VK_SCROLL     = 0x91   # ScrollLock
VK_PAUSE      = 0x13
VK_SNAPSHOT   = 0x2C

# ==================== 完整按键映射 ====================
KEY_NAMES = {
    # 修饰键（左右区分）
    VK_LSHIFT:   "LSHIFT",
    VK_RSHIFT:   "RSHIFT",
    VK_LCONTROL: "LCONTROL",
    VK_RCONTROL: "RCONTROL",
    VK_LMENU:    "LALT",
    VK_RMENU:    "RALT",
    VK_LWIN:     "LWIN",
    VK_RWIN:     "RWIN",
    # 通用修饰键（默认指向左键）
    0x10: "SHIFT",
    0x11: "CTRL",
    0x12: "ALT",
    # 控制键
    VK_SPACE:  "SPACE",
    VK_ENTER:  "ENTER",
    VK_TAB:    "TAB",
    VK_CAPITAL: "CAPSLOCK",
    VK_NUMLOCK: "NUMLOCK",
    VK_SCROLL:  "SCROLLLOCK",
    VK_PAUSE:   "PAUSE",
    VK_SNAPSHOT: "PRINTSCREEN",
    # 功能键 F1-F12
    0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4",
    0x74: "F5", 0x75: "F6", 0x76: "F7", 0x77: "F8",
    0x78: "F9", 0x79: "F10", 0x7A: "F11", 0x7B: "F12",
    # 小键盘数字 0-9
    0x60: "NUMPAD0", 0x61: "NUMPAD1", 0x62: "NUMPAD2",
    0x63: "NUMPAD3", 0x64: "NUMPAD4", 0x65: "NUMPAD5",
    0x66: "NUMPAD6", 0x67: "NUMPAD7", 0x68: "NUMPAD8",
    0x69: "NUMPAD9",
    # 小键盘运算符及其他
    0x6A: "MULTIPLY",   # *
    0x6B: "ADD",        # +
    0x6C: "SEPARATOR",  # 分隔符（通常为Enter）
    0x6D: "SUBTRACT",   # -
    0x6E: "DECIMAL",    # .
    0x6F: "DIVIDE",     # /
    # 其他常用键（可选）
    0x08: "BACKSPACE", 0x1B: "ESCAPE",
    0x21: "PAGE_UP",   0x22: "PAGE_DOWN",
    0x23: "END",       0x24: "HOME",
    0x25: "LEFT",      0x26: "UP",
    0x27: "RIGHT",     0x28: "DOWN",
    0x2D: "INSERT",    0x2E: "DELETE",
}

# 反向映射（字符串 → 虚拟键码）
KEY_CODES = {
    "LSHIFT": VK_LSHIFT, "RSHIFT": VK_RSHIFT,
    "LCONTROL": VK_LCONTROL, "RCONTROL": VK_RCONTROL,
    "LALT": VK_LMENU, "RALT": VK_RMENU,
    "LWIN": VK_LWIN, "RWIN": VK_RWIN,
    "SHIFT": VK_LSHIFT, "CTRL": VK_LCONTROL, "ALT": VK_LMENU,
    "SPACE": VK_SPACE, "ENTER": VK_ENTER, "TAB": VK_TAB,
    "CAPSLOCK": VK_CAPITAL, "NUMLOCK": VK_NUMLOCK, "SCROLLLOCK": VK_SCROLL,
    "PAUSE": VK_PAUSE, "PRINTSCREEN": VK_SNAPSHOT,
    "BACKSPACE": 0x08, "ESCAPE": 0x1B,
    "PAGE_UP": 0x21, "PAGE_DOWN": 0x22,
    "END": 0x23, "HOME": 0x24,
    "LEFT": 0x25, "UP": 0x26, "RIGHT": 0x27, "DOWN": 0x28,
    "INSERT": 0x2D, "DELETE": 0x2E,
    # 小键盘
    "NUMPAD0": 0x60, "NUMPAD1": 0x61, "NUMPAD2": 0x62,
    "NUMPAD3": 0x63, "NUMPAD4": 0x64, "NUMPAD5": 0x65,
    "NUMPAD6": 0x66, "NUMPAD7": 0x67, "NUMPAD8": 0x68,
    "NUMPAD9": 0x69,
    "MULTIPLY": 0x6A, "ADD": 0x6B, "SUBTRACT": 0x6D,
    "DECIMAL": 0x6E, "DIVIDE": 0x6F,
    # 功能键
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
    "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
    "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
}

# 补充字母 A-Z
for i in range(26):
    code = 0x41 + i
    name = chr(ord('A') + i)
    KEY_NAMES[code] = name
    KEY_CODES[name] = code
    KEY_CODES[name.lower()] = code

# 补充数字 0-9（主键盘区）
for i in range(10):
    code = 0x30 + i
    name = str(i)
    KEY_NAMES[code] = name
    KEY_CODES[name] = code

# ==================== 辅助函数 ====================
class Timer:
    """
    装饰器，用于计算函数运行时间。

    参数:
        show: 是否输出耗时，默认为 True。

    示例:
        @Timer()
        def func():
            print(f'func name: {func.__name__}')

        @Timer(show=False)
        def silent_func():
            pass
    """

    def __init__(self, show: bool = True):
        self.show = show

    def __call__(self, func: Callable) -> Callable:
        # import time
        # from functools import wraps
        # from typing import Callable, Any

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if self.show:
                start = time.perf_counter()  # 高精度计时
            result = func(*args, **kwargs)
            if self.show:
                elapsed = (time.perf_counter() - start)
                print(f"执行 {func.__name__} 耗时 {elapsed:.3f}S({elapsed * 1000:.2f} ms)")
            return result
        return wrapper

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def MAKELONG(x, y):
    return (y << 16) | (x & 0xFFFF)

def find_rock_window():
    windows = []
    def callback(hwnd, lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        if "洛克王国：世界" in buf.value:
            windows.append(hwnd)
        return True
    WNDENUMPROC = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return windows[0] if windows else None

def get_client_rect(hwnd):
    rect = (ctypes.c_long * 4)()
    user32.GetClientRect(hwnd, rect)
    return rect[2], rect[3]

def get_key_state(vk_code):
    """返回按键的 toggle 状态（0/1）"""
    state = user32.GetKeyState(vk_code)
    return (state & 1) != 0

# ==================== 底层消息发送 ====================
def send_mouse_msg(hwnd, x, y, msg, wParam=0, timeout=1):
    timeout = timeout / 1000
    if not hwnd:
        return False
    lparam = MAKELONG(x, y)
    user32.PostMessageW(hwnd, msg, wParam, lparam)
    if timeout > 0:
        time.sleep(timeout)
    return True

def send_key_msg(hwnd, vk_code, is_down=True, timeout=1):
    timeout = timeout / 1000
    if not hwnd:
        return False
    scan = user32.MapVirtualKeyW(vk_code, 0)
    msg = WM_KEYDOWN if is_down else WM_KEYUP
    if is_down:
        lParam = (scan << 16) | 0x00000001
    else:
        lParam = (scan << 16) | 0xC0000001
    user32.SendMessageW(hwnd, msg, vk_code, lParam)
    if timeout > 0:
        time.sleep(timeout)
    return True

def active_window(hwnd, delay=10):
    if not hwnd:
        return False
    user32.SendMessageW(hwnd, WM_ACTIVATE, WA_ACTIVE, 0)
    if delay > 0:
        time.sleep(delay / 1000)
    return True

# ==================== 统一模拟接口 ====================
def simulate_input(hwnd, input_type, **kwargs):
    if not hwnd:
        return False
    delay = kwargs.get('delay', 0)

    # 鼠标
    if input_type in ('click', 'down', 'up', 'move'):
        x = kwargs.get('x')
        y = kwargs.get('y')
        if x is None or y is None:
            log("缺少坐标")
            return False
        button = kwargs.get('button', 'left')
        btn_map = {
            'left':   (MK_LBUTTON, WM_LBUTTONDOWN, WM_LBUTTONUP),
            'right':  (MK_RBUTTON, WM_RBUTTONDOWN, WM_RBUTTONUP),
            'middle': (MK_MBUTTON, WM_MBUTTONDOWN, WM_MBUTTONUP)
        }
        if button not in btn_map:
            log("不支持的鼠标按键")
            return False
        mk, msg_down, msg_up = btn_map[button]
        active_window(hwnd)
        send_mouse_msg(hwnd, x, y, WM_MOUSEMOVE, 0, 1)
        if input_type == 'move':
            return True
        if input_type == 'down':
            return send_mouse_msg(hwnd, x, y, msg_down, mk, delay)
        if input_type == 'up':
            return send_mouse_msg(hwnd, x, y, msg_up, 0, delay)
        if input_type == 'click':
            send_mouse_msg(hwnd, x, y, msg_down, mk, delay)
            return send_mouse_msg(hwnd, x, y, msg_up, 0, 1)

    # 键盘
    elif input_type == 'key':
        action = kwargs.get('action', 'press').lower()
        key = kwargs.get('key')
        if key is None:
            log("缺少键名")
            return False
        if isinstance(key, str):
            vk_code = KEY_CODES.get(key.upper())
            if vk_code is None:
                log(f"未知键名: {key}")
                return False
        else:
            vk_code = key
        if action == 'down':
            return send_key_msg(hwnd, vk_code, True, delay)
        if action == 'up':
            return send_key_msg(hwnd, vk_code, False, delay)
        if action == 'press':
            send_key_msg(hwnd, vk_code, True, delay)
            return send_key_msg(hwnd, vk_code, False, 1)
        log(f"不支持的键盘动作: {action}")
        return False
    else:
        log(f"不支持的输入类型: {input_type}")
        return False

# ==================== 技能序列（左Shift） ====================
# @Timer()
def execute_diu_qiu_sequence(hwnd, x, y):
    if not hwnd:
        return False
    # 左键按下→延迟175ms→左键松开
    simulate_input(hwnd, 'click', x=x, y=y, button='left',
                   delay=random.randint(175, 177))
    # 延迟130ms
    time.sleep(random.randint(130, 132) / 1000)
    # 左Shift按下→延迟25ms→左Shift松开
    simulate_input(hwnd, 'key', action='press', key='LSHIFT',
                   delay=random.randint(23, 25))
    # 延迟20ms
    time.sleep(random.randint(20, 22) / 1000)
    return True



# ==================== 技能序列改键位（F1 F2） ====================
# @Timer()
def execute_diu_qiu_sequence_fork(hwnd, x, y):
    if not hwnd:
        return False
    # 左键按下→延迟175ms→左键松开
    simulate_input(hwnd, 'key', action='press', key='F1',
                   delay=random.randint(175, 177))
    # 延迟130ms
    time.sleep(random.randint(130, 132) / 1000)
    # 左Shift按下→延迟25ms→左Shift松开
    simulate_input(hwnd, 'key', action='press', key='F2',
                   delay=random.randint(23, 25))
    # 延迟20ms
    time.sleep(random.randint(20, 22) / 1000)
    return True

# ==================== 丢球HID模拟版 ====================
# @Timer()
def execute_diu_qiu_sequence_hid(hwnd, x, y):
    if not hwnd:
        return False
    dev.mouse.click("left", hold_ms=175)    # 左键按住150ms
    time.sleep(random.randint(130, 132) / 1000)
    dev.mouse.click("right", hold_ms=25)    # 右键按住65ms
    return True
# ==================== 测试程序 ====================
@Timer()
def test(count=1):
    hwnd = find_rock_window()
    if not hwnd:
        log("未找到游戏窗口，请确认标题包含'洛克王国：世界'")
        return
    # log(f"找到窗口句柄: {hwnd}")
    w, h = get_client_rect(hwnd)
    # log(f"客户区大小: {w} x {h}")
    click_x, click_y = w // 2, h // 2
    user32.SendMessageW(hwnd, WM_ACTIVATE, WA_ACTIVE, 0)
    # time.sleep(0.01)
    for i in range(count):
        if execute_diu_qiu_sequence(hwnd, click_x, click_y):
            log(f"[{time.strftime('%H:%M:%S')}] 坐标: ({click_x}, {click_y}) 丢球完成")
        else:
            log("丢球失败")


# ==================== 主程序 ====================
@Timer()
def main():
    log("=" * 50)
    log("后台键鼠统一模拟 - 洛克王国丢球脚本 (使用左Shift + 完整键位)")
    log("规则：CapsLock开启时暂停丢球，NumLock关闭时退出脚本")
    log("=" * 50)

    hwnd = find_rock_window()
    if not hwnd:
        log("未找到游戏窗口，请确认标题包含'洛克王国：世界'")
        return
    log(f"找到窗口句柄: {hwnd}")
    w, h = get_client_rect(hwnd)
    log(f"客户区大小: {w} x {h}")

    click_x, click_y = w // 2, h // 2
    log(f"点击坐标: ({click_x}, {click_y})")
    log("开始循环丢球 (Ctrl+C 停止)...\n")

    paused = False
    count = 0
    try:
        while True:
            # 1. 检测 NumLock 状态 - 关闭则退出
            if not get_key_state(VK_NUMLOCK):
                log(f"NumLock 已关闭，脚本停止，总丢球: {count}")
                break

            # 2. 检测 CapsLock 状态 - 开启则暂停丢球
            if get_key_state(VK_CAPITAL):
                if not paused:
                    log("CapsLock 开启，暂停丢球...")
                    paused = True
                time.sleep(0.1)   # 暂停期间低频率轮询
                continue
            else:
                if paused:
                    log("CapsLock 关闭，恢复丢球")
                    paused = False

            # 执行丢球序列
            if execute_diu_qiu_sequence(hwnd, click_x, click_y):
                # 可选：取消注释以每步都输出
                count += 1
                log(f"[{time.strftime('%H:%M:%S')}] 坐标: ({click_x}, {click_y}) 丢球完成, 已丢{count}球")
                pass
            else:
                log("丢球失败")

            # 短暂延时，避免 CPU 满载
            time.sleep(0.002)

    except KeyboardInterrupt:
        log(f"\n用户中断，脚本退出，总丢球: {count}")

if __name__ == "__main__":
    main()