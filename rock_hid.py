#!/usr/bin/env python3
"""
洛克王国世界 - USB HID 工具类
封装窗口检测 + 安全校验 + 自动选最快传输层 (USB/TCP/SSH)
"""
import time, ctypes
from ctypes import wintypes
from hid_device import HIDInput

USER32 = ctypes.windll.user32

class WindowInfo:
    __slots__ = ('hwnd','left','top','right','bottom','width','height','cx','cy')
    def __init__(self, hwnd, left, top, right, bottom):
        self.hwnd=hwnd; self.left=left; self.top=top
        self.right=right; self.bottom=bottom
        self.width=right-left; self.height=bottom-top
        self.cx=left+self.width//2; self.cy=top+self.height//2

class RockHID:
    def __init__(self, transport=None, game_keywords=('洛克','王国')):
        self.hid = HIDInput(transport)
        self.game_keywords = game_keywords
        self._window = None

    # ── 窗口查找 ──────────────────────────────

    def find_window(self):
        results = []
        def cb(hwnd, _):
            if USER32.IsWindowVisible(hwnd):
                buf = ctypes.create_unicode_buffer(256)
                n = USER32.GetWindowTextW(hwnd, buf, 256)
                if n > 0 and any(kw in buf.value for kw in self.game_keywords):
                    r = wintypes.RECT()
                    USER32.GetWindowRect(hwnd, ctypes.byref(r))
                    results.append(WindowInfo(hwnd, r.left, r.top, r.right, r.bottom))
            return True
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        USER32.EnumWindows(WNDENUMPROC(cb), 0)
        if not results: return None
        results.sort(key=lambda v: -v.width * v.height)
        self._window = results[0]; return self._window

    @property
    def window(self):
        if self._window is None: self.find_window()
        return self._window

    @property
    def center(self):
        w = self.window; return (w.cx, w.cy) if w else None

    # ── 安全校验 ──────────────────────────────

    def is_safe(self, win=None):
        w = win or self.window
        if not w: return False
        if USER32.GetForegroundWindow() != w.hwnd: return False
        p = wintypes.POINT(); USER32.GetCursorPos(ctypes.byref(p))
        return w.left <= p.x <= w.right and w.top <= p.y <= w.bottom

    def ensure_safe(self, win=None):
        w = win or self.window
        if not w: print("[RockHID] 窗口未找到"); return False
        if USER32.GetForegroundWindow() != w.hwnd:
            print("[RockHID] 拦截: 窗口非前台"); return False
        p = wintypes.POINT(); USER32.GetCursorPos(ctypes.byref(p))
        if not (w.left <= p.x <= w.right and w.top <= p.y <= w.bottom):
            print(f"[RockHID] 拦截: 光标({p.x},{p.y})在窗口外"); return False
        return True

    def focus(self):
        w = self.window
        if w: USER32.SetForegroundWindow(w.hwnd); time.sleep(0.5)

    # ── 便捷操作 ──────────────────────────────

    def move_cursor(self, x, y):
        USER32.SetCursorPos(x, y)

    def click(self, x=None, y=None, hold_ms=175):
        if x is not None and y is not None:
            self.move_cursor(x, y); time.sleep(0.1)
        if not self.ensure_safe(): return False
        self.hid.click("left", hold_ms); return True

    def right_click(self, x=None, y=None, hold_ms=65):
        if x is not None and y is not None:
            self.move_cursor(x, y); time.sleep(0.1)
        if not self.ensure_safe(): return False
        self.hid.mouse.click("right", hold_ms); return True

    def shift_tap(self, hold_ms=35):
        if not self.ensure_safe(): return False
        self.hid.cmd(f"ktap:LSHIFT:{hold_ms}"); return True

    def throw_sequence(self, x=None, y=None, left_ms=175, gap_ms=20, shift_ms=35):
        if x is not None and y is not None:
            self.move_cursor(x, y); time.sleep(0.15)
        if not self.ensure_safe(): return False
        self.hid.cmd(f"throw:{left_ms}:{gap_ms}:{shift_ms}"); return True

    def batch_throw(self, n=10, t1_ms=175, gap_ms=20, t2_ms=35, iv_ms=0):
        if not self.ensure_safe(): return False
        self.hid.batch_throw(n, t1_ms, gap_ms, t2_ms, iv_ms); return True

    def cmd(self, command):
        return self.hid.cmd(command)

    @property
    def transport_name(self):
        return self.hid.transport_name
