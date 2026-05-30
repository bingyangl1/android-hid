#!/data/data/com.termux/files/usr/bin/python3
"""
USB HID Gadget 配置脚本 (通用版)
自动检测 UDC / CONFIGFS / Python 路径，支持环境变量覆盖

用法:
  python3 phone_hid_dual.py              → 配置 HID + 启动 daemon
  python3 phone_hid_dual.py restore       → 恢复 USB 为正常模式

环境变量覆盖:
  HID_UDC              UDC 名称 (自动检测)
  HID_CONFIGFS_PATH    配置路径 (默认 /config/usb_gadget)
  HID_GADGET_NAME      Gadget 名称 (默认 g1)
  HID_VID              厂商 ID  (默认 0x22d9)
  HID_PID              产品 ID  (默认 0x2769)
  HID_SERIAL           序列号  (默认 1234567890)
  HID_MANUFACTURER     厂商名  (默认 Generic)
  HID_PRODUCT          产品名  (默认 HID Bridge)
  HID_MAX_POWER        MaxPower (默认 500)
  HID_DAEMON_PATH      daemon 路径 (默认 phone/hid_daemon.py)
"""
import os, time, sys, subprocess, json

# ── 自动检测 ──────────────────────────────────

def detect_udc():
    udcs = sorted(os.listdir("/sys/class/udc/"))
    for d in udcs:
        if "dummy" not in d:
            return d
    return udcs[0] if udcs else None

def detect_configfs():
    for mount in ["/config", "/sys/kernel/config", "/sys/config"]:
        if os.path.isdir(f"{mount}/usb_gadget"):
            return f"{mount}/usb_gadget"
    # 尝试找挂载点
    try:
        r = subprocess.run(["mount"], capture_output=True, text=True)
        for line in r.stdout.split("\n"):
            if "configfs" in line:
                parts = line.split()
                if len(parts) >= 3:
                    return f"{parts[2]}/usb_gadget"
    except: pass
    return "/config/usb_gadget"

# ── 配置 ──────────────────────────────────────

UDC = os.environ.get("HID_UDC") or detect_udc()
GADGET = os.environ.get("HID_GADGET_NAME", "g1")
CONFIGFS = os.environ.get("HID_CONFIGFS_PATH") or detect_configfs()
G = f"{CONFIGFS}/{GADGET}"

SAVED_CONFIG = "/data/local/tmp/usb_config_saved"
PID_FILE = "/data/local/tmp/hid_daemon.pid"

CONFIG = {
    "idVendor":      os.environ.get("HID_VID", "0x22d9"),
    "idProduct":     os.environ.get("HID_PID", "0x2769"),
    "serialnumber":  os.environ.get("HID_SERIAL", "1234567890"),
    "manufacturer":  os.environ.get("HID_MANUFACTURER", "Generic"),
    "product":       os.environ.get("HID_PRODUCT", "USB HID Bridge"),
    "MaxPower":      os.environ.get("HID_MAX_POWER", "500"),
    "config_label":  "HID+Serial",
}

def log(s): print(f"  {s}")
def read_file(p):
    try:
        with open(p) as f: return f.read().strip()
    except: return ""
def write_file(p, data):
    with open(p, 'wb' if isinstance(data, bytes) else 'w') as f: f.write(data)

def save_usb_state():
    config = read_file("/data/property/persist.sys.usb.config") or ""
    log(f"saved USB config: '{config}'")
    write_file(SAVED_CONFIG, config or "mtp,adb")

def restore_usb():
    print("=== USB 恢复 ===")
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f: pid = int(f.read().strip())
            os.kill(pid, 15); time.sleep(1)
        except: pass
        try: os.unlink(PID_FILE)
        except: pass
    for fn in ["/data/local/tmp/hid_daemon.quit"]:
        try: os.unlink(fn)
        except: pass
    if os.path.isdir(G):
        log("unbinding UDC...")
        try: write_file(f"{G}/UDC", "")
        except: pass
        time.sleep(1)
        b1 = f"{G}/configs/b.1"
        if os.path.isdir(b1):
            for name in list(os.listdir(b1)):
                p = os.path.join(b1, name)
                if os.path.islink(p): os.unlink(p); log(f"unlinked {name}")
        for d in ["configs/b.1/strings/0x409", "configs/b.1", "strings/0x409"]:
            try: os.rmdir(f"{G}/{d}")
            except: pass
        for func in ["hid.keyboard", "hid.mouse", "g.serial"]:
            fp = f"{G}/functions/{func}"
            if os.path.isdir(fp):
                try: os.rmdir(fp)
                except: log(f"rmdir {func} failed")
        for d in ["functions", "configs"]:
            try: os.rmdir(f"{G}/{d}")
            except: pass
        try: os.rmdir(G); log("gadget removed")
        except: pass
    saved = read_file(SAVED_CONFIG)
    config = saved if saved else "mtp,adb"
    log(f"sys.usb.config = {config}")
    subprocess.run(["setprop", "sys.usb.config", config], capture_output=True)
    time.sleep(2)
    subprocess.run(["start", "adbd"], capture_output=True)
    time.sleep(1)
    log(f"USB: '{read_file(f'/sys/class/udc/{UDC}/state')}'" if UDC else "USB restore done")
    print("=== Done ===")

# ── HID 描述符 ────────────────────────────────

# 鼠标: 4 字节报告, 5 按键 + X/Y/滚轮
HID_MOUSE_DESC = bytes([
    0x05,0x01,0x09,0x02,0xA1,0x01,      # Generic Desktop > Mouse
    0x09,0x01,0xA1,0x00,                #   Physical > Pointer
    0x05,0x09,                           #     Button
    0x19,0x01,0x29,0x05,                 #     Usage Min 1, Max 5 (左/右/中/X1/X2)
    0x15,0x00,0x25,0x01,                #     Log Min 0, Max 1
    0x95,0x05,0x75,0x01,0x81,0x02,      #     5 bits 按键
    0x95,0x01,0x75,0x03,0x81,0x03,      #     3 bits padding
    0x05,0x01,                           #     Generic Desktop
    0x09,0x30,0x09,0x31,0x09,0x38,      #     X, Y, Wheel
    0x15,0x81,0x25,0x7F,                #     Log Min -127, Max 127
    0x75,0x08,0x95,0x03,0x81,0x06,      #     3 bytes (X/Y/Wheel) 相对
    0xC0,0xC0
])

# 键盘: 8 字节报告 (标准, 支持所有 104+ 键)
HID_KBD_DESC = bytes([
    0x05,0x01,0x09,0x06,0xA1,0x01,      # Generic Desktop > Keyboard
    0x05,0x07,                           #   Keyboard/Keypad
    0x19,0xE0,0x29,0xE7,                #   Usage Min 224 (LCtrl), Max 231 (RGui)
    0x15,0x00,0x25,0x01,                #   Log Min 0, Max 1
    0x75,0x01,0x95,0x08,0x81,0x02,      #   8 modifier bits
    0x95,0x01,0x75,0x08,0x81,0x03,      #   1 byte reserved
    0x95,0x05,0x75,0x01,                #   5 LED bits (NumLock, CapsLock, ScrollLock, Compose, Kana)
    0x05,0x08,                           #   LEDs page
    0x19,0x01,0x29,0x05,0x91,0x02,      #   Output (LEDs)
    0x95,0x01,0x75,0x03,0x91,0x03,      #   3 bits padding for LEDs
    0x95,0x06,0x75,0x08,                #   6 键位槽
    0x15,0x00,0x25,0x65,                #   Log Min 0, Max 101
    0x05,0x07,                           #   Keyboard/Keypad
    0x19,0x00,0x29,0x65,                #   Usage Min 0, Max 101
    0x81,0x00,                           #   Input (Data,Array)
    0xC0
])

# ── 配置函数 ─────────────────────────────────

def ensure_function(name, kind="hid"):
    fp = f"{G}/functions/{kind}.{name}"
    if os.path.isdir(fp):
        try: os.rmdir(fp)
        except:
            log(f"can't remove {kind}.{name}")
            return fp
    os.makedirs(fp, exist_ok=True)
    return fp

def safe_makedirs(path):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)

def setup_hid(start_daemon=True):
    global UDC
    if not UDC:
        print("ERROR: No UDC found!"); sys.exit(1)

    print(f"UDC: {UDC}")
    print(f"Gadget: {G}")
    save_usb_state()

    print("\n[1] Stop adbd")
    subprocess.run(["stop", "adbd"], capture_output=True); time.sleep(1)

    print("[2] sys.usb.config = none")
    subprocess.run(["setprop", "sys.usb.config", "none"]); time.sleep(1)

    print("[3] Unbind UDC")
    if os.path.isdir(G):
        try: write_file(f"{G}/UDC", "")
        except: pass
        time.sleep(1)

    print("[4] Init gadget")
    safe_makedirs(f"{G}/strings/0x409")
    safe_makedirs(f"{G}/configs/b.1/strings/0x409")
    for k, v in CONFIG.items():
        if k in ("config_label",): continue
        try: write_file(f"{G}/{k}", v)
        except: log(f"write {k} failed")

    write_file(f"{G}/configs/b.1/strings/0x409/configuration", CONFIG["config_label"])
    write_file(f"{G}/configs/b.1/MaxPower", CONFIG["MaxPower"])

    # Clean old links
    b1 = f"{G}/configs/b.1"
    for name in list(os.listdir(b1)):
        p = os.path.join(b1, name)
        if os.path.islink(p): os.unlink(p)

    # 5. Keyboard
    print("[5] hid.keyboard")
    kp = ensure_function("keyboard", "hid")
    write_file(f"{kp}/protocol", b'1')
    write_file(f"{kp}/subclass", b'1')
    write_file(f"{kp}/report_length", b'8')
    write_file(f"{kp}/report_desc", HID_KBD_DESC)
    os.symlink(kp, f"{b1}/hid.keyboard"); log("linked")

    # 6. Mouse (5 buttons)
    print("[6] hid.mouse (5 buttons)")
    mp = ensure_function("mouse", "hid")
    write_file(f"{mp}/protocol", b'2')
    write_file(f"{mp}/subclass", b'0')
    write_file(f"{mp}/report_length", b'4')
    write_file(f"{mp}/report_desc", HID_MOUSE_DESC)
    os.symlink(mp, f"{b1}/hid.mouse"); log("linked")

    # 7. ACM Serial (控制通道, 可选)
    print("[7] g.serial (ACM)")
    sp = f"{G}/functions/g.serial"
    try:
        os.makedirs(sp, exist_ok=True)
        os.symlink(sp, f"{b1}/g.serial"); log("linked")
    except Exception as e:
        log(f"g.serial not supported: {e}")
        log("(HID+TCP daemon will work without serial)")

    # 8. Bind UDC
    print(f"[8] Bind UDC ({UDC})")
    try:
        write_file(f"{G}/UDC", UDC); log("success")
    except Exception as e: log(f"error: {e}")
    time.sleep(3)

    # 9. Verify
    print("[9] Verify")
    print(f"  UDC = '{read_file(f'{G}/UDC')}'")
    state = read_file(f'/sys/class/udc/{UDC}/state') if UDC else "?"
    print(f"  state = '{state}'")
    for d in ["/dev/hidg0", "/dev/hidg1", "/dev/ttyGS0"]:
        print(f"  {d}: {'present' if os.path.exists(d) else 'MISSING!'}")

    # Trigger driver load
    for dev in ["/dev/hidg1", "/dev/hidg0"]:
        try:
            fd = os.open(dev, os.O_WRONLY)
            os.write(fd, b"\x00" * (4 if "hidg1" in dev else 8))
            os.close(fd)
        except: pass

    # 10. Daemon
    if start_daemon:
        print("\n[10] Start daemon")
        daemon = find_daemon()
        if daemon:
            my_python = sys.executable or "/data/data/com.termux/files/usr/bin/python3"
            log(f"starting {daemon} ...")
            subprocess.Popen(
                [my_python, daemon],
                stdout=open("/data/local/tmp/hid_daemon.log", "w"),
                stderr=subprocess.STDOUT)
        else:
            log("hid_daemon.py not found")

    print(f"\n=== HID ready: /dev/hidg0(kbd) /dev/hidg1(mouse) /dev/ttyGS0(serial) ===")
    print(f"Restore: python3 {sys.argv[0]} restore")

def find_daemon():
    candidates = [
        os.environ.get("HID_DAEMON_PATH", ""),
        os.path.join(os.path.dirname(__file__) or ".", "phone", "hid_daemon.py"),
        os.path.join(os.path.dirname(__file__) or ".", "hid_daemon.py"),
        "/data/data/com.termux/files/home/phone/hid_daemon.py",
        "./phone/hid_daemon.py",
        "phone/hid_daemon.py",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return os.path.abspath(path)
    return None

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("restore", "reset", "--restore", "--reset"):
        restore_usb()
    else:
        setup_hid(start_daemon="--no-daemon" not in sys.argv and "--no-start" not in sys.argv)
