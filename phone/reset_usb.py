#!/data/data/com.termux/files/usr/bin/python3
"""
紧急 USB 恢复脚本 - 当一切卡死时用
用法: python3 reset_usb.py
"""
import os, subprocess, time

UDC = "a600000.dwc3"
G = "/config/usb_gadget/g1"

print("=== USB 紧急恢复 ===")

# stop daemon
for f in ["/data/local/tmp/hid_daemon.pid", "/data/local/tmp/hid_daemon.quit"]:
    try: os.unlink(f)
    except: pass

# kill python processes holding HID
subprocess.run(["pkill", "-f", "hid_daemon.py"], capture_output=True)
time.sleep(1)

# unbind UDC
if os.path.isdir(G):
    try:
        with open(f"{G}/UDC", "w") as f: f.write("")
    except: pass
    time.sleep(1)

# restore android USB
subprocess.run(["setprop", "sys.usb.config", "mtp,adb"])
time.sleep(2)
subprocess.run(["start", "adbd"])

print("USB restored. Unplug/replug cable if needed.")
