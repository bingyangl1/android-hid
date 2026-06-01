#!/usr/bin/env python3
"""
洛克王国世界 - USB HID 丢球器 CLI
"""
from rock_hid import RockHID
import sys, time, ctypes
from ctypes import wintypes

hid = RockHID()

def usage():
    print("""
Usage:
  rock_hid_clicker.py click [x y]         Left click at (x,y) or cursor
  rock_hid_clicker.py right [x y]         Right click
  rock_hid_clicker.py shift               Tap Shift (throw ball)
  rock_hid_clicker.py throw [x y]         Throw sequence at (x,y) or cursor
  rock_hid_clicker.py setpos x y          Move cursor only
  rock_hid_clicker.py center [action]     click/right/throw at window center
  rock_hid_clicker.py test-hid            Test both HID devices
    """, end="")

def main():
    if len(sys.argv) < 2: usage(); return
    cmd = sys.argv[1]

    if cmd == "test-hid":
        print("Testing HID...")
        hid.hid.cmd("mclick:left:175"); time.sleep(0.5)
        hid.hid.cmd("mclick:right:65"); time.sleep(0.5)
        hid.hid.cmd("ktap:LSHIFT:35")
        print("HID test done"); return

    if cmd == "setpos":
        x, y = int(sys.argv[2]), int(sys.argv[3])
        hid.move_cursor(x, y); print(f"Moved to ({x},{y})"); return

    if not hid.window:
        print("Game window not found"); return

    if cmd == "center":
        action = sys.argv[2] if len(sys.argv) > 2 else "click"
        w = hid.window
        print(f"Game: {w.width}x{w.height} center ({w.cx},{w.cy})")
        if action == "click": hid.click(w.cx, w.cy); print("Clicked center")
        elif action == "right": hid.right_click(w.cx, w.cy); print("Right clicked center")
        elif action == "throw": hid.throw_sequence(w.cx, w.cy); print("Threw at center")
        else: print(f"Unknown action: {action}")
        return

    if cmd in ("click", "right", "throw"):
        has_xy = len(sys.argv) >= 4
        x = int(sys.argv[2]) if has_xy else None
        y = int(sys.argv[3]) if has_xy else None
        if cmd == "click": hid.click(x, y)
        elif cmd == "right": hid.right_click(x, y)
        else: hid.throw_sequence(x, y)
        p = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(p))
        print(f"{cmd.title()} at ({p.x},{p.y})"); return

    if cmd == "shift":
        hid.shift_tap(); print("Shift tapped"); return

    print(f"Unknown command: {cmd}")

if __name__ == "__main__": main()
