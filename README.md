# LUOKE HID — USB HID Bridge for Rooted Android

通过 Root 手机的 USB HID Gadget 实现硬件级键鼠模拟。HID 报告由真实 USB 总线传输，无法被反作弊（ACE/EAC/BattlEye）与软件注入区分。

## Architecture

```
PC (HIDInput)                          Phone (rooted Android)
─────────────                          ────────────────────
                                        phone_hid_dual.py
                                           │
        ┌── RNDISTransport (USB 网卡) ───→┤
        │   TCP:8023 over USB cable        ├── /dev/hidg0 (keyboard)
        │                                  ├── /dev/hidg1 (mouse)
        ├── TCPTransport  (WiFi) ────────→┤
        │   TCP:8023 over WiFi             └── phone/hid_daemon.py
        │                                              │
        └── SSHTransport  (fallback) ────→ select() ───┘
            exec code via SSH pipe          stdin / TCP / serial
```

Transport auto-degradation: **RNDIS → TCP → SSH**

| Layer | Latency | Cable | Depends On |
|-------|---------|-------|------------|
| **RNDIS** | ~1ms | ✅ USB data | Phone kernel: `gsi.rndis` |
| **TCP** | ~20ms | ❌ WiFi | Phone daemon running |
| **SSH** | ~500ms | ❌ WiFi | Phone SSHD + Termux |

## Project Structure

```
F:\luoke/
├── phone_hid_dual.py      Phone: USB gadget config (RNDIS + HID)
├── PC/
│   ├── hid_device.py       PC: 4-layer transport + key/mouse API
│   └── __init__.py
├── phone/
│   ├── hid_daemon.py       Phone: daemon (TCP:8023)
│   ├── exec.py             SSH one-shot Python executor
│   └── reset_usb.py        Emergency USB restore
├── example/
│   ├── rock_hid.py         Game integration wrapper
│   ├── rock_hid_clicker.py CLI throw tool
│   └── 丢球_HID.py          Throw script for Rock Kingdom
├── docs/
│   ├── RNDIS_MODE.md       USB wired control channel guide
│   ├── ADB_MODE.md         ADB trigger mode guide
│   └── DUCKSCRIPT.md       DuckyScript reference (planned)
├── archive/                Legacy scripts
└── README.md
```

## Quick Start

### Phone: Configure HID + RNDIS

```bash
# Push to phone (adjust paths for your setup)
scp -P <ssh_port> phone_hid_dual.py phone/ <user>@<phone_ip>:~/ -r

# SSH into phone and run
ssh -p <ssh_port> <user>@<phone_ip> \
  "su -c 'python3 ~/phone_hid_dual.py'"
```

This will:
1. Stop ADB, release USB
2. Create USB Gadget with HID keyboard + mouse + RNDIS
3. Set RNDIS IP (192.168.42.2/24) on phone
4. Start `hid_daemon.py` listening on `0.0.0.0:8023`
5. PC detects HID Keyboard + Mouse + RNDIS virtual Ethernet

### PC: Use HIDInput

```python
from PC.hid_device import HIDInput

dev = HIDInput()                    # Auto: RNDIS > TCP > SSH
dev.mouse.click("left", 175)        # Left click, 175ms hold
dev.mouse.move(100, -50)            # Relative move X+100, Y-50
dev.keyboard.tap("A", 40)           # Tap A for 40ms
dev.keyboard.tap("LSHIFT", 35)      # Tap Shift
dev.keyboard.press("W")             # Hold W
dev.keyboard.release()              # Release all keys
dev.cmd("throw:175:20:35")          # Raw command: left+shift sequence
```

### Restore USB (Phone)

```bash
python3 phone_hid_dual.py restore
# Emergency: python3 phone/reset_usb.py
```

## Configuration

### Phone (env vars)

| Variable | Default | Description |
|----------|---------|-------------|
| `HID_UDC` | auto | UDC name (e.g. `a600000.dwc3`) |
| `HID_CONFIGFS_PATH` | `/config/usb_gadget` | ConfigFS mount |
| `HID_TCP_PORT` | `8023` | Daemon TCP port |
| `HID_GADGET_NAME` | `g1` | Gadget name |
| `HID_VID` | `0x22d9` | Vendor ID |
| `HID_PID` | `0x2769` | Product ID |

### PC (env vars)

| Variable | Default | Description |
|----------|---------|-------------|
| `LUOKE_HOST` | `root@<phone>` | SSH user@host |
| `LUOKE_SSHPORT` | `8022` | SSH port |
| `LUOKE_TCPHOST` | `<phone>` | TCP daemon host |
| `LUOKE_TCPPORT` | `8023` | TCP daemon port |
| `LUOKE_RNDISHOST` | `192.168.42.2` | RNDIS phone IP |
| `LUOKE_PYTHON` | phone python path | Phone Python binary |
| `LUOKE_HOME` | phone home dir | Phone home directory |

## Supported Inputs

### Mouse (5 buttons + wheel)

`left`, `right`, `middle`, `x1`, `x2` · relative X/Y (−127 to +127) · vertical wheel

Report: `[buttons][X][Y][wheel]` (4 bytes)

### Keyboard (full 104-key set)

- A-Z, 0-9, F1-F12
- Modifiers: `LCTRL` `RCTRL` `LSHIFT` `RSHIFT` `LALT` `RALT` `LGUI` `RGUI`
- Aliases: `CTRL` `SHIFT` `ALT` `GUI`
- Nav: `UP` `DOWN` `LEFT` `RIGHT` `HOME` `END` `PGUP` `PGDN`
- Edit: `BKSP` `DEL` `INS` `TAB` `ENTER` `ESC`
- Numpad: `NUM0`-`NUM9` `NUM_DOT` `NUM_ENTER` `NUM_PLUS` `NUM_MINUS` `NUM_SLASH` `NUM_ASTERISK`
- Lock: `CAPSLOCK` `NUMLOCK` `SCROLLLOCK`
- Other: `PAUSE` `PRINTSCREEN` `MENU`

Combos:
```python
dev.keyboard.press("LCTRL")    # Hold Ctrl
dev.keyboard.tap("C", 40)       # Tap C (with Ctrl held)
dev.keyboard.release()          # Release all
```

## Transport Details

### RNDIS (preferred)
Phone sets up `gsi.rndis` in gadget config. PC gets a virtual Ethernet adapter. TCP:8023 flows over the USB cable. Requires phone kernel support (`gsi.rndis`).

### TCP (WiFi fallback)
Phone daemon listens on `0.0.0.0:8023`. Connect over WiFi when no RNDIS available.

### SSH (emergency fallback)
Executes Python code via SSH pipe. `phone/exec.py` decodes and runs base64-encoded Python. No daemon required.

## Adapting to Other Phones

1. **Find UDC**: `ls /sys/class/udc/` — pick the non-dummy entry
2. **Check ConfigFS**: `ls /config/usb_gadget/` — if missing: `mount -t configfs none /config`
3. **Check RNDIS**: `ls /config/usb_gadget/g1/functions/gsi.rndis` — if missing, falls back to TCP

Common UDCs:

| SoC | UDC |
|-----|-----|
| Snapdragon 865/870/888/8G1/8G2 | `a600000.dwc3` |
| Dimensity | `musb-hdrc` / `11200000.usb` |
| Kirin | `ff100000.dwc3` |
| Exynos | `dwc3` |

## Troubleshooting

| Problem | Check |
|---------|-------|
| No HID on PC | `cat /sys/class/udc/<UDC>/state` should say `configured` |
| No RNDIS netif | Kernel lacks `gsi.rndis`; auto-falls to TCP |
| Daemon won't start | Log: `cat /data/local/tmp/hid_daemon.log` |
| Need to restore ADB | `python3 phone_hid_dual.py restore` |
| Kill daemon manually | `touch /data/local/tmp/hid_daemon.quit` |
