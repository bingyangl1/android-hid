#!/usr/bin/env python3
"""
蓝牙 HID 键鼠传输 + 模拟
             延迟     可靠性
  ADB forward ~5ms    ★★★★★ (USB/WiFi ADB, 首选)
  TCP WiFi    ~20ms   ★★★★ (WiFi 直连, 兜底)
  SSH tunnel  ~500ms  ★★★ (最后手段)

自动降级: ADB forward → TCP → SSH

用法:
  dev = HIDInput()                → 自动选最快
  dev = HIDInput("adb")           → 强制 ADB forward
  dev = HIDInput("tcp")           → 强制 TCP (WiFi)
  dev = HIDInput("ssh")           → 强制 SSH

  dev.mouse.click("left", 175)
  dev.mouse.click("x1", 40)
  dev.keyboard.tap("LSHIFT", 35)
  dev.keyboard.tap("F5")
  dev.cmd("mclick:x1:175")        → 原始命令

环境变量:
  LUOKE_HOST       SSH 地址     (默认 root@192.168.5.170)
  LUOKE_SSHPORT    SSH 端口     (默认 8022)
  LUOKE_TCPPORT    TCP 端口     (默认 8023)
  LUOKE_TCPHOST    TCP 地址     (默认 192.168.5.170)
  LUOKE_ADB        adb 路径     (默认 adb)
"""
import subprocess, time, socket, os

# ═══════════════════════════════════════════════
#  配置
# ═══════════════════════════════════════════════

def env(k, default):
    return os.environ.get(f"LUOKE_{k}", default)

CFG = {
    "host":      env("HOST",      "root@192.168.5.170"),
    "ssh_port":  env("SSHPORT",   "8022"),
    "tcp_host":  env("TCPHOST",   "192.168.5.170"),
    "tcp_port":  int(env("TCPPORT", "8023")),
    "adb":       env("ADB",       "adb"),
}

_SSH_CTL = "/tmp/ssh-ctl-luoke"

def _ssh_cmd(command):
    return ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
            "-o", "ControlMaster=auto", "-o", f"ControlPath={_SSH_CTL}",
            "-o", "ControlPersist=600",
            "-p", CFG["ssh_port"], CFG["host"], command]

# ═══════════════════════════════════════════════
#  HID 键码映射 (同步 APP CommandParser.kt)
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

def parse_key(key):
    k = key.upper().strip()
    if not k:
        return 0, 0
    if k in HID:
        return HID[k], 0
    if len(k) == 1 and k.upper() in HID:
        return HID[k.upper()], 0
    return 0, 0

# ═══════════════════════════════════════════════
#  Transport
# ═══════════════════════════════════════════════

class TransportError(Exception): pass

class Transport:
    name = "abstract"
    def cmd(self, command): raise NotImplementedError
    def close(self): pass
    def __del__(self):
        try: self.close()
        except: pass

class _SocketTransport(Transport):
    """TCP socket 公共逻辑"""
    def _connect(self, host, port, timeout):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(timeout)
        self._sock.connect((host, port))

    def cmd(self, command):
        self._sock.send((command + "\n").encode())
        return self._sock.recv(4096).decode(errors="replace").strip()

    def close(self):
        if hasattr(self, '_sock'):
            self._sock.close()

class ADBForwardTransport(_SocketTransport):
    """通过 adb forward 转发 TCP 端口"""
    name = "adb"

    def __init__(self, port=None, timeout=10):
        port = port or CFG["tcp_port"]
        adb = CFG["adb"]
        # 清理旧的 forward
        subprocess.run([adb, "forward", "--remove", f"tcp:{port}"],
                       capture_output=True)
        # 建立 forward: PC localhost:port → 手机 localhost:port
        r = subprocess.run([adb, "forward", f"tcp:{port}", f"tcp:{port}"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise TransportError(f"adb forward failed: {r.stderr.strip()}")
        self._port = port
        self._connect("127.0.0.1", port, timeout)

    def close(self):
        super().close()
        subprocess.run([CFG["adb"], "forward", "--remove", f"tcp:{self._port}"],
                       capture_output=True)

class TCPTransport(_SocketTransport):
    """WiFi 直连 TCP"""
    name = "tcp"

    def __init__(self, host=None, port=None, timeout=10):
        host = host or CFG["tcp_host"]
        port = port or CFG["tcp_port"]
        self._connect(host, port, timeout)

class SSHTransport(Transport):
    """SSH 隧道转发到手机 TCP server"""
    name = "ssh"

    def __init__(self, timeout=10):
        port = CFG["tcp_port"]
        # 检查 SSH 连通性
        r = subprocess.run(_ssh_cmd("echo ok"),
                           capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            raise TransportError(f"ssh unreachable: {r.stderr[:100]}")
        self._port = port

    def cmd(self, command):
        # 通过 SSH 用 nc 转发到手机 TCP server
        escaped = command.replace("'", "'\\''")
        r = subprocess.run(
            _ssh_cmd(f"echo '{escaped}' | nc -q 1 localhost {self._port}"),
            capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise TransportError(f"ssh cmd failed: {r.stderr[:100]}")
        return r.stdout.strip()

# ── 自动选择 ─────────────────────────────────

def auto_transport():
    for name, cls in [("adb", ADBForwardTransport), ("tcp", TCPTransport)]:
        try:
            t = cls()
            print(f"[HID] {name}: ok")
            return t
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
        self.t.cmd(f"mpress:{button.lower()}")
        return self

    def release(self, button=None):
        self.t.cmd(f"mrelease:{button}" if button else "mrelease:")
        return self

    def click(self, button="left", hold_ms=40):
        self.t.cmd(f"mclick:{button}:{hold_ms}")
        return self

    def move(self, dx=0, dy=0, wheel=0):
        self.t.cmd(f"mmove:{dx}:{dy}:{wheel}")
        return self

class HIDKeyboard:
    def __init__(self, transport): self.t = transport

    def press(self, key):
        self.t.cmd(f"kpress:{key}")
        return self

    def release(self, *a):
        self.t.cmd("krelease:")
        return self

    def tap(self, key, hold_ms=40):
        self.t.cmd(f"ktap:{key}:{hold_ms}")
        return self

class HIDInput:
    def __init__(self, transport_spec=None, show_latency=False):
        self._show_latency = show_latency
        if transport_spec is None:
            self._t = auto_transport()
        elif isinstance(transport_spec, Transport):
            self._t = transport_spec
        elif isinstance(transport_spec, str):
            s = transport_spec.lower()
            if s.startswith("adb"):
                self._t = ADBForwardTransport()
            elif s.startswith("tcp"):
                p = s.split(":")
                h = p[1] if len(p) > 1 else CFG["tcp_host"]
                n = int(p[2]) if len(p) > 2 else CFG["tcp_port"]
                self._t = TCPTransport(h, n)
            elif s.startswith("ssh"):
                self._t = SSHTransport()
            else:
                raise ValueError(f"unknown transport: {transport_spec}")
        else:
            raise TypeError(f"expected str/Transport, got {type(transport_spec)}")
        self.mouse = HIDMouse(self._t)
        self.keyboard = HIDKeyboard(self._t)
        self._latency_buf = []

    def click(self, button="left", hold_ms=40):
        self.mouse.click(button, hold_ms)

    def key(self, key, hold_ms=40):
        self.keyboard.tap(key, hold_ms)

    def press(self, key):
        self.keyboard.press(key)

    def release(self, *a):
        self.keyboard.release()

    def cmd(self, command):
        t0 = time.perf_counter()
        result = self._t.cmd(command)
        elapsed = (time.perf_counter() - t0) * 1000
        if self._show_latency:
            print(f"[{elapsed:.1f}ms] {command} → {result}")
        self._latency_buf.append(elapsed)
        return result

    def batch_throw(self, n=10, t1_ms=175, gap_ms=20, t2_ms=35, iv_ms=0):
        r = self._t.cmd(f"bthrow:{n}:{t1_ms}:{gap_ms}:{t2_ms}:{iv_ms}")
        return r.startswith("ok")

    def latency_stats(self):
        """返回延迟统计 {avg, min, max, p50, p99, count}"""
        buf = self._latency_buf
        if not buf:
            return None
        s = sorted(buf)
        n = len(s)
        return {
            "avg":  sum(s) / n,
            "min":  s[0],
            "max":  s[-1],
            "p50":  s[n // 2],
            "p99":  s[int(n * 0.99)] if n >= 100 else s[-1],
            "count": n,
        }

    def latency_str(self):
        """格式化延迟统计"""
        st = self.latency_stats()
        if not st:
            return "no data"
        return (f"avg={st['avg']:.1f}ms min={st['min']:.1f}ms "
                f"max={st['max']:.1f}ms p50={st['p50']:.1f}ms "
                f"p99={st['p99']:.1f}ms n={st['count']}")

    @property
    def transport_name(self): return self._t.name

if __name__ == "__main__":
    d = HIDInput(show_latency=True)
    print(f"Transport: {d.transport_name}")
    r = d.cmd("ping")
    print(f"Ping: {r}")
    print(d.latency_str())
