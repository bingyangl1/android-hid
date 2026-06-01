#!/data/data/com.termux/files/usr/bin/python3
"""
USB HID Daemon (通用版)
常驻进程, 保持 hidg0/hidg1 打开, select() 轮询多通道
通道: /dev/ttyGS0 (USB串口) + TCP:8023 (WiFi) + stdin (SSH/pipe)

所有鼠标按键 + 完整键盘映射
"""
import os, time, selectors, socket, sys, signal

HID_MOUSE = os.environ.get("HID_MOUSE", "/dev/hidg1")
HID_KBD   = os.environ.get("HID_KBD",   "/dev/hidg0")
TCP_PORT  = int(os.environ.get("HID_TCP_PORT", "8023"))
BAIL_FILE = os.environ.get("HID_BAIL_FILE", "/data/local/tmp/hid_daemon.quit")

fm = fk = None
mouse_btn_state = 0  # 鼠标当前按下的按键状态

# ── 鼠标按键 ──────────────────────────────────
BTN = {"left":1,"right":2,"middle":4,"x1":8,"x2":16}

# ── 完整键盘映射 ────────────────────────────
HID = {
    "A":4,"B":5,"C":6,"D":7,"E":8,"F":9,"G":10,"H":11,"I":12,"J":13,
    "K":14,"L":15,"M":16,"N":17,"O":18,"P":19,"Q":20,"R":21,"S":22,
    "T":23,"U":24,"V":25,"W":26,"X":27,"Y":28,"Z":29,
    "0":39,"1":30,"2":31,"3":32,"4":33,"5":34,"6":35,"7":36,"8":37,"9":38,
    "F1":58,"F2":59,"F3":60,"F4":61,"F5":62,"F6":63,"F7":64,"F8":65,
    "F9":66,"F10":67,"F11":68,"F12":69,
    "ENTER":40,"ESC":41,"ESCAPE":41,"BKSP":42,"BACKSPACE":42,"TAB":43,"SPACE":44,
    "MINUS":45,"-":45,"EQUAL":46,"=":46,
    "OPEN_BRACKET":47,"[":47,"CLOSE_BRACKET":48,"]":48,
    "BACKSLASH":49,"\\":49,
    "SEMICOLON":51,";":51,"QUOTE":52,"'":52,"GRAVE":53,"`":53,
    "COMMA":54,",":54,"PERIOD":55,".":55,"SLASH":56,"/":56,
    "CAPSLOCK":57,
    "PRINTSCREEN":70,"SCROLLLOCK":71,"PAUSE":72,
    "INSERT":73,"INS":73,"HOME":74,"PAGEUP":75,"PGUP":75,
    "DELETE":76,"DEL":76,"END":77,"PAGEDOWN":78,"PGDN":78,
    "UP":82,"DOWN":81,"LEFT":80,"RIGHT":79,
    "NUMLOCK":83,
    "NUM_SLASH":84,"NUM_ASTERISK":85,"NUM_MINUS":86,
    "NUM_PLUS":87,"NUM_ENTER":88,
    "NUM1":89,"NUM2":90,"NUM3":91,"NUM4":92,"NUM5":93,
    "NUM6":94,"NUM7":95,"NUM8":96,"NUM9":97,"NUM0":98,
    "NUM_DOT":99,
    "MENU":101,"APPS":101,"APPLICATION":101,
    # 修饰键别名 (0xE0-0xE7, 用 bitmask 处理)
    "LCTRL":0xE0,"RCTRL":0xE4,
    "LSHIFT":0xE1,"RSHIFT":0xE5,
    "LALT":0xE2,"RALT":0xE6,
    "LGUI":0xE3,"RGUI":0xE7,
    "CTRL":0xE0,"SHIFT":0xE1,"ALT":0xE2,"GUI":0xE3,
}
MOD_BITS = {
    0xE0:1, 0xE4:16, 0xE1:2, 0xE5:32,
    0xE2:4, 0xE6:64, 0xE3:8, 0xE7:128,
}
MOD_BY_NAME = {
    "LCTRL":1,"RCTRL":16,"LSHIFT":2,"RSHIFT":32,
    "LALT":4,"RALT":64,"LGUI":8,"RGUI":128,
    "CTRL":1,"SHIFT":2,"ALT":4,"GUI":8,
}

def _kb(mod, *keys):
    b = bytearray(8); b[0] = mod
    for i,k in enumerate(keys[:6]): b[2+i] = k
    return bytes(b)

def parse_key(key):
    k = key.upper().strip()
    if not k: return None, None
    # 直接 modifier bitmask
    if k in MOD_BY_NAME: return 0, MOD_BY_NAME[k]
    if k in HID:
        v = HID[k]
        if v > 0xFF:
            return v, 0  # 修饰键 alias, 后面按 0xE0-0xE7 处理
        return 0, v
    # 单字符
    if len(k) == 1:
        uk = k.upper()
        if uk in HID:
            v = HID[uk]
            if v <= 0xFF: return 0, v
    return None, None

def exec_cmd(line):
    try:
        parts = line.strip().split(":")
        cmd = parts[0]; a = parts[1:]
        return _exec(cmd, a)
    except Exception as e:
        return f"err:{e}"

def _exec(cmd, a):
    global fm, fk, mouse_btn_state

    # ── 鼠标 ──
    if cmd == "mclick":
        btn = a[0].lower() if a else "left"
        t = int(a[1]) / 1000 if len(a) > 1 else 0.04
        v = BTN.get(btn, 1)
        os.write(fm, bytes([v,0,0,0])); time.sleep(t); os.write(fm, b"\x00\x00\x00\x00")
        return "ok"
    if cmd == "mpress":
        global mouse_btn_state
        btn = a[0].lower() if a else "left"
        v = BTN.get(btn, 1)
        mouse_btn_state |= v
        os.write(fm, bytes([mouse_btn_state,0,0,0])); return "ok"
    if cmd == "mrelease":
        if a:
            btn = a[0].lower(); v = BTN.get(btn, 0)
            mouse_btn_state &= ~v
        else:
            mouse_btn_state = 0
        os.write(fm, bytes([mouse_btn_state,0,0,0])); return "ok"
    if cmd == "mmove":
        dx = int(a[0]) if a else 0
        dy = int(a[1]) if len(a) > 1 else 0
        ww = int(a[2]) if len(a) > 2 else 0
        def c(v): return v & 0xFF if v >= 0 else (256+v) & 0xFF
        os.write(fm, bytes([0, c(dx), c(dy), c(ww)])); return "ok"

    # ── 键盘 ──
    if cmd == "ktap":
        usage, mod = parse_key(a[0])
        t = int(a[1]) / 1000 if len(a) > 1 else 0.04
        if usage is None and mod == 0: return f"err:unknown key {a[0]}"
        if mod > 0 and mod < 256:
            # modifier bitmask
            os.write(fk, _kb(mod, 0)); time.sleep(t); os.write(fk, _kb(0))
        elif usage and usage <= 0xFF:
            os.write(fk, _kb(0, usage)); time.sleep(t); os.write(fk, _kb(0))
        else:
            modv = MOD_BITS.get(usage, 0)
            os.write(fk, _kb(modv, 0)); time.sleep(t); os.write(fk, _kb(0))
        return "ok"
    if cmd == "kpress":
        usage, mod = parse_key(a[0])
        if usage is None and mod == 0: return f"err:unknown key {a[0]}"
        if mod > 0 and mod < 256:
            os.write(fk, _kb(mod, 0))
        elif usage and usage <= 0xFF:
            os.write(fk, _kb(0, usage))
        else:
            os.write(fk, _kb(MOD_BITS.get(usage, 0), 0))
        return "ok"
    if cmd == "krelease":
        os.write(fk, _kb(0)); return "ok"

    # ── 丢球 (兼容旧格式) ──
    if cmd == "throw":
        t1 = int(a[0]) / 1000 if a else 0.175
        gap = int(a[1]) / 1000 if len(a) > 1 else 0.02
        t2 = int(a[2]) / 1000 if len(a) > 2 else 0.035
        os.write(fm, b"\x01\x00\x00\x00"); time.sleep(t1); os.write(fm, b"\x00\x00\x00\x00")
        time.sleep(gap)
        os.write(fk, _kb(2, 0)); time.sleep(t2); os.write(fk, _kb(0))
        return "ok"
    if cmd == "bthrow":
        n = int(a[0]) if a else 10
        t1 = int(a[1]) / 1000 if len(a) > 1 else 0.175
        gap = int(a[2]) / 1000 if len(a) > 2 else 0.02
        t2 = int(a[3]) / 1000 if len(a) > 3 else 0.035
        iv = int(a[4]) / 1000 if len(a) > 4 else 0.5
        for i in range(n):
            os.write(fm, b"\x01\x00\x00\x00"); time.sleep(t1); os.write(fm, b"\x00\x00\x00\x00")
            time.sleep(gap)
            os.write(fk, _kb(2, 0)); time.sleep(t2); os.write(fk, _kb(0))
            if i < n - 1: time.sleep(iv)
        return "ok"

    # ── 原始写入 ──
    if cmd == "hidwrite":
        d = a[0]; data = bytes.fromhex(a[1]); t = int(a[2]) / 1000 if len(a) > 2 else 0
        fd = fm if d == "mouse" else fk
        os.write(fd, data)
        if t > 0: time.sleep(t); os.write(fd, b"\x00" * len(data))
        return "ok"

    # ── 控制 ──
    if cmd == "ping": return "pong"
    if cmd == "quit": return "ok"
    return f"err:unknown cmd {cmd}"

# ── 设备打开 ─────────────────────────────────

def open_hid():
    global fm, fk
    for d, name in [(HID_MOUSE, "mouse"), (HID_KBD, "kbd")]:
        for _ in range(30):
            try:
                fd = os.open(d, os.O_WRONLY)
                if name == "mouse": fm = fd
                else: fk = fd
                print(f"  {name}: {d} opened"); break
            except OSError: time.sleep(0.3)
        else:
            print(f"  FAILED {d}")

# ── 主循环 ───────────────────────────────────

def main():
    global fm, fk
    print("=== USB HID Daemon ===")
    open_hid()
    if fm is None or fk is None:
        print("HID devices unavailable, exiting"); sys.exit(1)

    sel = selectors.DefaultSelector()

    # Serial (USB ACM)
    for dev in os.environ.get("HID_SERIAL_DEVS", "/dev/ttyGS0,/dev/ttyGS1,/dev/ttyACM0").split(","):
        try:
            fd = os.open(dev.strip(), os.O_RDWR | os.O_NONBLOCK)
            sel.register(fd, selectors.EVENT_READ, data=("serial", fd, os.read, fd))
            print(f"  {dev.strip()}: opened"); break
        except OSError: continue

    # TCP listener
    tcp_sock = None
    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        host = os.environ.get("HID_TCP_HOST", "0.0.0.0")
        tcp_sock.bind((host, TCP_PORT)); tcp_sock.listen(5); tcp_sock.setblocking(False)
        sel.register(tcp_sock, selectors.EVENT_READ, data=("listener", tcp_sock, None))
        print(f"  TCP:{host}:{TCP_PORT}: listening")
    except Exception as e:
        print(f"  TCP:{TCP_PORT}: {e}")
        if tcp_sock: tcp_sock.close()

    # stdin (SSH pipe)
    sel.register(sys.stdin, selectors.EVENT_READ, data=("stdin", sys.stdin.fileno(), os.read, sys.stdin))

    print("Daemon ready.")
    try: os.unlink(BAIL_FILE)
    except: pass

    while True:
        try:
            if os.path.exists(BAIL_FILE): print("Quit file detected"); break
        except: pass
        try:
            events = sel.select(timeout=1.0)
        except OSError:
            time.sleep(0.1); continue
        for key, _ in events:
            kind, obj, reader, *extra = key.data
            fileobj = extra[0] if extra else obj
            try:
                if kind == "listener":
                    conn, addr = obj.accept()
                    conn.setblocking(False)
                    sel.register(conn, selectors.EVENT_READ,
                                 data=("tcp", conn, lambda o, n: o.recv(n)))
                    print(f"  TCP: {addr[0]} connected")
                    continue
                data = reader(obj, 4096)
                if not data:
                    print(f"  {kind}: closed")
                    sel.unregister(fileobj)
                    if hasattr(fileobj, "close"): fileobj.close()
                    continue
                for line in data.decode(errors="replace").split("\n"):
                    line = line.strip()
                    if not line: continue
                    resp = exec_cmd(line) + "\n"
                    if kind == "tcp":
                        obj.sendall(resp.encode())
                    else:
                        try: os.write(obj if isinstance(obj, int) else obj.fileno(), resp.encode())
                        except OSError: pass
            except (OSError, BlockingIOError): continue

    if fm: os.close(fm)
    if fk: os.close(fk)
    sel.close()
    print("Daemon stopped")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    main()
