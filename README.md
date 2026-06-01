# LUOKE HID — USB HID Bridge for Rooted Android

通过 Root 手机实现 USB 硬件级键鼠模拟，绕过反作弊（ACE/EAC/BattlEye）的软件注入检测。

## Architecture

```
PC                                        Phone (rooted Android)
──                                        ────────────────────
PC/hid_device.py (RNDISTransport)
  │
  ├─ RNDISTransport ─── USB RNDIS ──────→ phone/hid_daemon.py (TCP:8023)
  │   (USB虚拟网卡,有线)                    ├─ /dev/hidg0 (keyboard)
  ├─ TCPTransport  ─── WiFi TCP:8023 ───→ ├─ /dev/hidg1 (mouse)
  │   (无线,备选)                           └─ select() loop
  └─ SSHTransport  ─── SSH (兜底) ───────→ phone/exec.py
```

传输层自动降级（RNDIS → TCP → SSH）：

| 层 | 延迟 | 线缆 | 依赖 |
|----|------|------|------|
| **USB RNDIS** | ~0.5-2ms | ✅ USB 数据线 | 内核 `gsi.rndis` |
| **TCP/WiFi** | ~20ms | ❌ WiFi | 同网段 |
| **SSH** | ~500ms | ❌ WiFi | SSHD + Termux |

## Requirements

### Phone
- **Root access** (Magisk)
- **Termux** with Python 3
- Kernel with CONFIGFS + USB Gadget + `gsi.rndis` (高通 DWC3 平台内置)
- USB data cable

### PC
- Python 3.8+
- SSH client (for SSH fallback)

## Quick Start

### 1. Phone: Configure HID + RNDIS

```bash
# 推送到手机
scp -P 8022 phone_hid_dual.py phone/ root@192.168.5.170:~/ -r

# SSH 进手机执行
ssh -p 8022 root@192.168.5.170 \
  "su -c 'python3 /data/data/com.termux/files/home/phone_hid_dual.py'"
```

执行后：
1. 手机 Gadget 配置 HID 键盘 + 鼠标 + RNDIS 虚拟网卡
2. 手机 RNDIS IP: `192.168.42.2/24`
3. daemon 监听 `0.0.0.0:8023`
4. PC 端自动识别 RNDIS 虚拟网卡

### 2. PC: 使用 HIDInput

```python
from PC.hid_device import HIDInput

dev = HIDInput()                    # Auto: RNDIS > TCP > SSH
dev.mouse.click("left", 175)        # 左键点击, 按住175ms
dev.mouse.click("x1", 40)           # X1 (后退) 键
dev.mouse.move(100, -50)            # 相对移动
dev.keyboard.tap("LSHIFT", 35)      # 点按 Shift
dev.keyboard.tap("F5")              # 点按 F5
dev.keyboard.press("W")             # 按住 W
dev.keyboard.release()              # 松键
```

### 3. 恢复 USB（手机端）

```bash
python3 phone_hid_dual.py restore
# 或紧急恢复: python3 phone/reset_usb.py
```

## Project Structure

```
F:\luoke/
├── phone_hid_dual.py       手机: Gadget 配置 (RNDIS + HID)
├── PC/
│   ├── hid_device.py        PC: 四层传输 + 键鼠接口
│   └── __init__.py
├── phone/
│   ├── hid_daemon.py       手机: 常驻 daemon (TCP:8023)
│   ├── exec.py              SSH 单次代码执行器
│   ├── repeat_throw.py      SSH 批量丢球
│   └── reset_usb.py         USB 紧急恢复
├── example/
│   ├── rock_hid.py          洛克王国游戏集成
│   ├── rock_hid_clicker.py  CLI 丢球器
│   ├── 丢球_HID.py          丢球脚本（PC 端）
│   └── 丢球_手机版.py        丢球脚本（手机端直写 hidg）
├── docs/
│   ├── RNDIS_MODE.md        USB 有线控制通道指南
│   ├── ADB_MODE.md          ADB 触发模式指南
│   └── DUCKSCRIPT.md        DuckyScript 语法参考
├── archive/                  旧版本归档
├── Android-HID 项目改造任务书.md
└── README.md
```

## Configuration

Phone env vars:
```
HID_UDC              → UDC 名称 (自动检测)
HID_CONFIGFS_PATH    → ConfigFS 挂载路径 (默认 /config/usb_gadget)
HID_TCP_PORT         → Daemon TCP 端口 (默认 8023)
```

PC env vars:
```
LUOKE_HOST       → SSH user@host     (默认 root@192.168.5.170)
LUOKE_SSHPORT    → SSH 端口          (默认 8022)
LUOKE_TCPHOST    → TCP 主机地址      (默认 192.168.5.170)
LUOKE_TCPPORT    → TCP 端口          (默认 8023)
LUOKE_RNDISHOST  → RNDIS 手机 IP     (默认 192.168.42.2)
```

## Supported Inputs

### Mouse (5 键 + 滚轮)
- `left`, `right`, `middle`, `x1`, `x2`
- 相对移动 (−127 to +127)
- 垂直滚轮

### Keyboard (全 104 键 + 修饰键)
- A-Z, 0-9, F1-F12
- 修饰键: `LCTRL/RCTRL`, `LSHIFT/RSHIFT`, `LALT/RALT`, `LGUI/RGUI`
- 别名: `CTRL=LCTRL`, `SHIFT=LSHIFT`, `ALT=LALT`, `GUI=LGUI`

## Adapting to Other Phones

1. **UDC**: `ls /sys/class/udc/` — 用第一个非 dummy 的名称
2. **ConfigFS**: `ls /config/usb_gadget/` 应存在；否则 `mount -t configfs none /config`
3. **RNDIS**: 检查 `ls /config/usb_gadget/g1/functions/gsi.rndis` — 若无则自动降级 TCP

## Troubleshooting

**HID 不工作**: `cat /sys/class/udc/<UDC>/state` 应显示 `configured`

**RNDIS 无网络接口**: 内核无 `gsi.rndis`，自动降级 TCP (WiFi)

**Daemon 无法启动**: 检查日志 `/data/local/tmp/hid_daemon.log`

**恢复 ADB**: `python3 phone_hid_dual.py restore` 或 `python3 phone/reset_usb.py`
