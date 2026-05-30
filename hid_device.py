#!/usr/bin/env python3
"""
USB HID 三层传输 + 全面键鼠模拟
          延迟   可靠性
 USB ACM   ~0.1ms ★★★★★ (数据线)
 TCP WiFi   ~20ms ★★★★
 SSH        ~500ms ★★★ (兜底)

用法:
  dev = HIDInput()              → 自动选最快
  dev = HIDInput("usb")         → 强制 USB COM
  dev = HIDInput("tcp")         → 强制 TCP (WiFi)
  dev = HIDInput("ssh")         → 强制 SSH

  dev.mouse.click("left", 175)
  dev.mouse.click("x1", 40)
  dev.keyboard.tap("LSHIFT", 35)
  dev.keyboard.tap("F5")
  dev.cmd("mclick:x1:175")      → 原始命令

环境变量:
  LUOKE_HOST      SSH IP     (默认 root@192.168.5.170)
  LUOKE_SSHPORT   SSH 端口   (默认 8022)
  LUOKE_TCPPORT   TCP 端口   (默认 8023)
  LUOKE_TCPHOST   TCP 地址   (默认 192.168.5.170)
  LUOKE_VID       COM 的 VID (默认 VID_22D9)
  LUOKE_PYTHON    手机 Python 路径
  LUOKE_HOME      手机 home 目录
"""
import subprocess, time, base64, socket, os, sys

# ═══════════════════════════════════════════════
#  配置
# ═══════════════════════════════════════════════

def env(k, default):
    return os.environ.get(f"LUOKE_{k}", default)

CFG = {
    "host":     env("HOST",     "root@192.168.5.170"),
    "ssh_port": env("SSHPORT",  "8022"),
    "tcp_host": env("TCPHOST",  "192.168.5.170"),
    "tcp_port": int(env("TCPPORT", "8023")),
    "com_vid":  env("VID",      "VID_22D9"),
    "python":   env("PYTHON",   "/data/data/com.termux/files/usr/bin/python3"),
    "home":     env("HOME",     "/data/data/com.termux/files/home"),
    "mouse":    "/dev/hidg1",
    "kbd":      "/dev/hidg0",
}

_EXEC = f"{CFG['home']}/exec.py"
_REPEAT_THROW = f"{CFG['home']}/repeat_throw.py"
_SSH_CTL = "/tmp/ssh-ctl-luoke"

def _ssh_cmd(command):
    return ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
            "-o", "ControlMaster=auto", "-o", f"ControlPath={_SSH_CTL}",
            "-o", "ControlPersist=600",
            "-p", CFG["ssh_port"], CFG["host"], "su", "-c", command]

# ═══════════════════════════════════════════════
#  鼠标/键盘映射 (同步 phone/hid_daemon.py)
# ═══════════════════════════════════════════════

BTN = {"left":1, "right":2, "middle":4, "x1":8, "x2":16}

HID = {
    "A":4,"B":5,"C":6,"D":7,"E":8,"F":9,"G":10,"H":11,"I":12,"J":13,
    "K":14,"L":15,"M":16,"N":17,"O":18,"P":19,"Q":20,"R":21,"S":22,
    "T":23,"U":24,"V":25,"W":26,"X":27,"Y":28,"Z":29,
    "0":39,"1":30,"2":31,"3":32,"4":33,"5":34,"6":35,"7":36,"8":37,"9":38,
    "F1":58,"F2":59,"F3":60,"F4":61,"F5":62,"F6":63,"F7":64,"F8":65,
    "F9":66,"F10":67,"F11":68,"F12":69,
    "ENTER":40,"ESC":41,"ESCAPE":41,"BKSP":42,"BACKSPACE":42,
    "TAB":43,"SPACE":44,
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
    "NUM6":94,"NUM7":95,"NUM8":96,"NUM9":97,"NUM0":98,"NUM_DOT":99,
    "MENU":101,"APPS":101,"APPLICATION":101,
    "LCTRL":0xE0,"RCTRL":0xE4,"LSHIFT":0xE1,"RSHIFT":0xE5,
    "LALT":0xE2,"RALT":0xE6,"LGUI":0xE3,"RGUI":0xE7,
    "CTRL":0xE0,"SHIFT":0xE1,"ALT":0xE2,"GUI":0xE3,
}
MOD_BITS = {0xE0:1,0xE4:16,0xE1:2,0xE5:32,0xE2:4,0xE6:64,0xE3:8,0xE7:128}
MOD_BY_NAME = {k.upper():v for k,v in {
    "LCTRL":1,"RCTRL":16,"LSHIFT":2,"RSHIFT":32,
    "LALT":4,"RALT":64,"LGUI":8,"RGUI":128,
    "CTRL":1,"SHIFT":2,"ALT":4,"GUI":8,
}.items()}

def parse_key(key):
    k = key.upper().strip()
    if not k: return 0, 0
    if k in MOD_BY_NAME: return 0, MOD_BY_NAME[k]
    if k in HID:
        v = HID[k]
        return v, 0
    if len(k) == 1:
        uk = k.upper()
        if uk in HID:
            return HID[uk], 0
    return 0, 0

# ═══════════════════════════════════════════════
#  Transport
# ═══════════════════════════════════════════════

class TransportError(Exception): pass

class Transport:
    name = "abstract"
    def cmd(self, command): raise NotImplementedError

class USBTransport(Transport):
    name = "usb"
    def __init__(self, vid=None, baud=115200, timeout=10):
        import serial, serial.tools.list_ports
        vid = vid or CFG["com_vid"]
        port = None
        for p in serial.tools.list_ports.comports():
            if vid in p.hwid: port = p.device; break
        if not port: raise TransportError(f"USB ({vid}) not found")
        self._ser = serial.Serial(port, baud, timeout=timeout)
        time.sleep(2); self._ser.reset_input_buffer()

    def cmd(self, command):
        self._ser.write((command + "\n").encode())
        return self._ser.readline().decode(errors="replace").strip()

class TCPTransport(Transport):
    name = "tcp"
    def __init__(self, host=None, port=None, timeout=10):
        host = host or CFG["tcp_host"]; port = port or CFG["tcp_port"]
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(timeout); self._sock.connect((host, port))

    def cmd(self, command):
        self._sock.send((command + "\n").encode())
        return self._sock.recv(4096).decode(errors="replace").strip()

class SSHTransport(Transport):
    name = "ssh"
    def cmd(self, command):
        py = self._compile(command)
        if not py: return "ok"
        enc = base64.b64encode(py.encode()).decode()
        r = subprocess.run(_ssh_cmd(f"{CFG['python']} {_EXEC} {enc}"),
                           capture_output=True, timeout=30, text=True)
        return "ok" if r.returncode == 0 else f"err:{r.stderr[:200]}"

    def batch_throw(self, n=10, t1_ms=175, gap_ms=20, t2_ms=35, iv_ms=0):
        r = subprocess.run(_ssh_cmd(
            f"{CFG['python']} {_REPEAT_THROW} {n} {t1_ms} {gap_ms} {t2_ms} {iv_ms}"),
            capture_output=True, timeout=300, text=True)
        return r.returncode == 0

    def _compile(self, command):
        parts = command.strip().split(":")
        c = parts[0]; a = parts[1:]

        def clip(v): return v & 0xFF if v >= 0 else (256+v) & 0xFF

        if c == "mclick":
            btn = a[0].lower() if a else "left"
            t = a[1] if len(a) > 1 else "40"
            v = BTN.get(btn, 1)
            return (f"import os,time;f=os.open('{CFG['mouse']}',1);"
                    f"os.write(f,bytes([{v},0,0,0]));time.sleep({t}/1000);"
                    f"os.write(f,b'\\x00'*4);os.close(f)")
        if c == "mpress":
            btn = a[0].lower() if a else "left"; v = BTN.get(btn, 1)
            return f"import os;f=os.open('{CFG['mouse']}',1);os.write(f,bytes([{v},0,0,0]));os.close(f)"
        if c == "mrelease":
            return f"import os;f=os.open('{CFG['mouse']}',1);os.write(f,b'\\x00'*4);os.close(f)"
        if c == "mmove":
            dx = int(a[0]) if a else 0; dy = int(a[1]) if len(a) > 1 else 0
            ww = int(a[2]) if len(a) > 2 else 0
            return (f"import os;f=os.open('{CFG['mouse']}',1);"
                    f"os.write(f,bytes([0,{clip(dx)},{clip(dy)},{clip(ww)}]));os.close(f)")

        if c == "ktap": return self._ktap(a)
        if c == "kpress":
            usage, mod = parse_key(a[0] if a else "")
            if mod and mod < 256:
                return f"import os;f=os.open('{CFG['kbd']}',1);os.write(f,bytes([{mod},0,0,0,0,0,0,0]));os.close(f)"
            if usage and usage <= 0xFF:
                return f"import os;f=os.open('{CFG['kbd']}',1);os.write(f,bytes([0,{usage},0,0,0,0,0,0]));os.close(f)"
            m = MOD_BITS.get(usage, 0)
            return f"import os;f=os.open('{CFG['kbd']}',1);os.write(f,bytes([{m},0,0,0,0,0,0,0]));os.close(f)"
        if c == "krelease":
            return f"import os;f=os.open('{CFG['kbd']}',1);os.write(f,b'\\x00'*8);os.close(f)"

        if c == "throw":
            t1 = a[0] if a else 175; gap = a[1] if len(a) > 1 else 20; t2 = a[2] if len(a) > 2 else 35
            return (f"import os,time;m=os.open('{CFG['mouse']}',1);k=os.open('{CFG['kbd']}',1);"
                    f"os.write(m,b'\\x01\\x00\\x00\\x00');time.sleep({t1}/1000);"
                    f"os.write(m,b'\\x00\\x00\\x00\\x00');time.sleep({gap}/1000);"
                    f"os.write(k,b'\\x02'+b'\\x00'*7);time.sleep({t2}/1000);"
                    f"os.write(k,b'\\x00'*8);os.close(m);os.close(k)")
        if c == "bthrow":
            n = int(a[0]) if a else 10; t1 = a[1] if len(a) > 1 else 175
            gap = a[2] if len(a) > 2 else 20; t2 = a[3] if len(a) > 3 else 35; iv = a[4] if len(a) > 4 else 0
            body = ""
            for _ in range(n):
                body += (f"os.write(m,b'\\x01\\x00\\x00\\x00');time.sleep({t1}/1000);"
                         f"os.write(m,b'\\x00\\x00\\x00\\x00');time.sleep({gap}/1000);"
                         f"os.write(k,b'\\x02'+b'\\x00'*7);time.sleep({t2}/1000);"
                         f"os.write(k,b'\\x00'*8);")
                if _ < n-1: body += f"time.sleep({iv}/1000);"
            return (f"import os,time;m=os.open('{CFG['mouse']}',1);k=os.open('{CFG['kbd']}',1);"
                    f"{body}os.close(m);os.close(k)")
        if c == "ping": return "print('pong')"
        return ""

    def _ktap(self, a):
        t = a[1] if len(a) > 1 else "40"
        usage, mod = parse_key(a[0] if a else "")
        if mod and mod < 256:
            return (f"import os,time;f=os.open('{CFG['kbd']}',1);"
                    f"os.write(f,bytes([{mod},0,0,0,0,0,0,0]));time.sleep({t}/1000);"
                    f"os.write(f,b'\\x00'*8);os.close(f)")
        if usage and usage <= 0xFF:
            return (f"import os,time;f=os.open('{CFG['kbd']}',1);"
                    f"os.write(f,bytes([0,{usage},0,0,0,0,0,0]));time.sleep({t}/1000);"
                    f"os.write(f,b'\\x00'*8);os.close(f)")
        m = MOD_BITS.get(usage, 0)
        return (f"import os,time;f=os.open('{CFG['kbd']}',1);"
                f"os.write(f,bytes([{m},0,0,0,0,0,0,0]));time.sleep({t}/1000);"
                f"os.write(f,b'\\x00'*8);os.close(f)")

# ── 自动选择 ─────────────────────────────────

def auto_transport():
    for name, cls in [("usb", USBTransport), ("tcp", TCPTransport)]:
        try:
            t = cls()
            print(f"[HID] {name}: ok"); return t
        except Exception as e:
            print(f"[HID] {name}: {e}")
    print("[HID] ssh fallback")
    return SSHTransport()

# ═══════════════════════════════════════════════
#  键鼠界面
# ═══════════════════════════════════════════════

class HIDMouse:
    def __init__(self, transport): self.t = transport

    def press(self, button="left"):
        btn = button.lower()
        v = BTN.get(btn, BTN.get(btn, 1))
        self.t.cmd(f"mpress:{btn}"); return self

    def release(self, button=None):
        if button:
            self.t.cmd(f"mrelease:{button}"); return self
        self.t.cmd("mrelease:"); return self

    def click(self, button="left", hold_ms=40):
        btn = {"left":"mclick","right":"mright","middle":"mmiddle",
               "x1":"mx1","x2":"mx2"}.get(button.lower(), "mclick")
        self.t.cmd(f"mclick:{button}:{hold_ms}"); return self

    def move(self, dx=0, dy=0, wheel=0):
        self.t.cmd(f"mmove:{dx}:{dy}:{wheel}"); return self

class HIDKeyboard:
    def __init__(self, transport): self.t = transport

    def press(self, key):
        self.t.cmd(f"kpress:{key}"); return self

    def release(self, *a):
        self.t.cmd("krelease:"); return self

    def tap(self, key, hold_ms=40):
        self.t.cmd(f"ktap:{key}:{hold_ms}"); return self

class HIDInput:
    def __init__(self, transport_spec=None):
        if transport_spec is None:
            self._t = auto_transport()
        elif isinstance(transport_spec, Transport):
            self._t = transport_spec
        elif isinstance(transport_spec, str):
            s = transport_spec.lower()
            if s.startswith("usb"): self._t = USBTransport()
            elif s.startswith("tcp"):
                p = s.split(":")
                h = p[1] if len(p) > 1 else CFG["tcp_host"]
                n = int(p[2]) if len(p) > 2 else CFG["tcp_port"]
                self._t = TCPTransport(h, n)
            elif s.startswith("ssh"): self._t = SSHTransport()
            else: raise ValueError(f"unknown transport: {transport_spec}")
        else:
            raise TypeError(f"expected str/Transport, got {type(transport_spec)}")
        self.mouse = HIDMouse(self._t)
        self.keyboard = HIDKeyboard(self._t)

    def click(self, button="left", hold_ms=40):
        self.mouse.click(button, hold_ms)

    def key(self, key, hold_ms=40):
        self.keyboard.tap(key, hold_ms)

    def press(self, key):
        self.keyboard.press(key)

    def release(self, *a):
        self.keyboard.release()

    def cmd(self, command):
        return self._t.cmd(command)

    def batch_throw(self, n=10, t1_ms=175, gap_ms=20, t2_ms=35, iv_ms=0):
        if isinstance(self._t, SSHTransport):
            return self._t.batch_throw(n, t1_ms, gap_ms, t2_ms, iv_ms)
        self._t.cmd(f"bthrow:{n}:{t1_ms}:{gap_ms}:{t2_ms}:{iv_ms}")
        return True

    @property
    def transport_name(self): return self._t.name

# ── 旧 API (兼容) ────────────────────────────

def run_py(code):
    enc = base64.b64encode(code.encode()).decode()
    r = subprocess.run(_ssh_cmd(f"{CFG['python']} {_EXEC} {enc}"),
                       capture_output=True, timeout=15, text=True)
    return r.returncode == 0

def batch_throw(n=10, t1_ms=175, gap_ms=50, t2_ms=35, iv_ms=500):
    r = subprocess.run(_ssh_cmd(
        f"{CFG['python']} {_REPEAT_THROW} {n} {t1_ms} {gap_ms} {t2_ms} {iv_ms}"),
        capture_output=True, timeout=300, text=True)
    return r.returncode == 0

if __name__ == "__main__":
    from pprint import pprint
    d = HIDInput()
    print(f"Transport: {d.transport_name}")
    r = d.cmd("ping")
    print(f"Ping: {r}")
