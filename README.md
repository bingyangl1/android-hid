# LUOKE HID — USB HID Bridge for Rooted Android

通过 Root 手机实现 USB 硬件级键鼠模拟，绕过反作弊（ACE/EAC/BattlEye）的软件注入检测。

## Architecture

```
PC                                          Phone (rooted Android)
──                                          ────────────────────
luoke_app.py
  │
  ▼ HIDInput()
  ├─ USBTransport ── USB ACM (COM port) ──→ hid_daemon.py
  │                                          ├─ /dev/hidg0 (keyboard)
  ├─ TCPTransport ── WiFi TCP:8023 ────────→ ├─ /dev/hidg1 (mouse)
  │                                          └─ select() loop
  └─ SSHTransport ── SSH (fallback) ───────→ exec.py / repeat_throw.py
```

Three transport layers (auto-selected in order):
| Layer | Latency | Cable needed | Phone daemon |
|-------|---------|-------------|--------------|
| **USB ACM** | ~0.1ms | ✅ USB data cable | hid_daemon.py |
| **TCP/WiFi** | ~20ms | ❌ WiFi only | hid_daemon.py |
| **SSH** | ~500ms | ❌ WiFi only | None (direct) |

## Requirements

### Phone
- **Root access** (Magisk recommended)
- **Termux** with Python 3
- Kernel with **CONFIGFS** + **USB Gadget** support (most LineageOS / custom kernels)
- USB cable for HID mode (`python3 phone_hid_dual.py` restores ADB/MTP on exit)

### PC
- Python 3.8+
- `pyserial` (optional, only needed for USB ACM mode): `pip install pyserial`
- SSH client (for fallback)

## Quick Start

### 1. Phone: Configure HID + Start Daemon

```bash
# Push scripts to phone
scp -P 8022 -r phone root@phone:/data/data/com.termux/files/home/
scp -P 8022 phone_hid_dual.py root@phone:/data/data/com.termux/files/home/

# SSH into phone and run
ssh -p 8022 root@phone "su -c 'python3 /data/data/com.termux/files/home/phone_hid_dual.py'"
```

This will:
1. Stop ADB
2. Create USB Gadget with HID keyboard + mouse + serial ACM
3. Start `hid_daemon.py` in background
4. PC should detect HID Keyboard + Mouse + COM port

### 2. PC: Use HIDInput

```python
from hid_device import HIDInput

dev = HIDInput()                    # Auto: USB > TCP > SSH
dev.mouse.click("left", 175)        # Left click, 175ms hold
dev.mouse.click("x1", 40)           # X1 (back) button
dev.mouse.move(100, -50)            # Relative move
dev.keyboard.tap("LSHIFT", 35)      # Tap LShift
dev.keyboard.tap("F5")              # Tap F5
dev.keyboard.tap("CTRL", 0)         # Modifier as tap (0ms = press only)
dev.keyboard.press("W")             # Hold W
dev.mouse.release("left")           # Release specific mouse button
dev.keyboard.release()              # Release all
```

### 3. Restore Normal USB (Phone)

```bash
python3 phone_hid_dual.py restore
# Or emergency kill: echo quit > /data/local/tmp/hid_daemon.quit && python3 reset_usb.py
```

## Configuration

Phone-side env vars:
```
HID_UDC              → UDC name (auto-detect)
HID_CONFIGFS_PATH    → ConfigFS mount (default /config/usb_gadget)
HID_TCP_PORT         → Daemon TCP port (default 8023)
```

PC-side env vars:
```
LUOKE_HOST     → SSH user@host (default root@192.168.5.170)
LUOKE_SSHPORT  → SSH port (default 8022)
LUOKE_TCPHOST  → TCP host for daemon (default 192.168.5.170)
LUOKE_TCPPORT  → TCP port (default 8023)
LUOKE_VID      → USB VID for COM detection (default VID_22D9)
```

## Supported Inputs

### Mouse (5 buttons + wheel)
- `left`, `right`, `middle`, `x1`, `x2` buttons
- Relative X/Y movement (8-bit, -127 to +127)
- Vertical wheel

### Keyboard (all standard keys)
- A-Z, 0-9
- F1-F12
- Modifiers: `LCTRL/RCTRL`, `LSHIFT/RSHIFT`, `LALT/RALT`, `LGUI/RGUI`
- Navigation: `UP/DOWN/LEFT/RIGHT`, `HOME/END/PGUP/PGDN`
- Editing: `INSERT/DELETE/BACKSPACE/TAB/ENTER/ESCAPE`
- Numpad: `NUM0-NUM9`, `NUM_SLASH/NUM_ASTERISK/NUM_MINUS/NUM_PLUS/NUM_DOT/NUM_ENTER`
- Lock keys: `CAPSLOCK/NUMLOCK/SCROLLLOCK`
- Other: `PRINTSCREEN/PAUSE/MENU`
- Aliases: `CTRL=LCTRL`, `SHIFT=LSHIFT`, `ALT=LALT`, `GUI=LGUI`, `ESC=ESCAPE`, `DEL=DELETE`, `INS=INSERT`, etc.

## Adapting to Other Phones

1. **Find UDC**: `ls /sys/class/udc/` — use the only entry (auto-detected)
2. **Verify ConfigFS**: `ls /config/usb_gadget/` should exist
3. **If not**, try: `mount -t configfs none /config` (or find existing mount via `mount | grep configfs`)
4. **Set env vars** if auto-detect fails

Common UDC names per SoC:
- Snapdragon (888/8Gen1/8Gen2): `a600000.dwc3`
- Snapdragon (865/870): `a600000.dwc3`
- MediaTek Dimensity: `musb-hdrc` or `11200000.usb`
- Exynos: `dwc3`
- Kirin: `ff100000.dwc3`

## Project Structure

```
luoke/
├── hid_device.py         PC端: 三层传输 + 键鼠接口
├── rock_hid.py           PC端: 洛克王国工具 (窗口检测 + 安全校验)
├── 秒丢2.5球.py          PC端: 丢球脚本
├── phone_hid_dual.py     手机: Gadget 配置 + 复原
├── phone/                 手机端脚本
│   ├── hid_daemon.py     常驻 daemon (USB ACM/TCP)
│   ├── reset_usb.py      紧急 USB 恢复
│   ├── exec.py           SSH 代码执行器 (遗留)
│   └── repeat_throw.py   SSH 批量丢球 (遗留)
├── _archive/              旧版本归档
└── 使用说明.md            中文详细文档
```

## Troubleshooting

**USB not detected on PC**: Unplug/replug cable, run setup again.

**No COM port appears**: Missing `g.serial` in gadget config. Verify `/dev/ttyGS0` on phone.

**HID device not showing**: Check UDC binding — `cat /sys/class/udc/<UDC>/state` should say `configured`.

**Daemon won't start**: Check logs at `/data/local/tmp/hid_daemon.log`

**Restore ADB**: `python3 phone_hid_dual.py restore` or emergency: `python3 phone/reset_usb.py`
