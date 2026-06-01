#!/usr/bin/env python3
"""
丢球 Demo - 使用 batch_throw（单次 SSH 执行 N 次丢球）
"""
from rock_hid import RockHID
import sys, time, ctypes

hid = RockHID()
w = hid.find_window()
if not w:
    print("Game window not found")
    sys.exit(1)

print(f"Window: {w.width}x{w.height}  center: ({w.cx},{w.cy})")

n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
interval = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3

hid.focus()
time.sleep(0.5)

if not hid.ensure_safe():
    print("Not safe (focus + cursor check)")
    sys.exit(1)

print(f"Throwing {n} balls via batch_throw...")
t0 = time.perf_counter()
# Move cursor to center first
hid.move_cursor(w.cx, w.cy)
time.sleep(0.1)
# Batch throw - all N throws in ONE SSH call
hid.batch_throw(n=n, t1_ms=175, gap_ms=50, t2_ms=35, iv_ms=int(interval * 1000))
elapsed = time.perf_counter() - t0
print(f"Done: {n} throws in {elapsed:.1f}s ({n/elapsed:.1f} throws/s)")
