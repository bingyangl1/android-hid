# LUOKE HID — 通过 Root 安卓手机实现 USB 硬件键鼠模拟

利用 Root 手机的 USB HID Gadget 将 PC 端发起的键盘/鼠标指令转化为真实 HID 报告，经 USB 总线直接发送给本机。反作弊系统（ACE / EAC / BattlEye）无法区分其与真正物理设备。

## 架构

```
PC (HIDInput)                          手机 (已 Root 安卓)
─────────────                          ────────────────────
                                         phone_hid_dual.py
                                            │
        ┌── RNDISTransport (USB 网卡) ────→┤
        │   TCP:8023 经 USB 数据线传输      ├── /dev/hidg0 (键盘)
        │                                   ├── /dev/hidg1 (鼠标)
        ├── TCPTransport  (WiFi) ─────────→┤
        │   TCP:8023 经 WiFi                └── phone/hid_daemon.py
        │                                               │
        └── SSHTransport  (兜底) ──────────→ select() ───┘
            SSH 管道执行 Python                stdin / TCP / 串口
```

传输层自动降级：**RNDIS → TCP → SSH**

| 传输层 | 延迟 | 需数据线 | 依赖条件 |
|--------|------|---------|----------|
| **RNDIS** | ~1ms | ✅ | 手机内核支持 `gsi.rndis` |
| **TCP** | ~20ms | ❌ WiFi | 手机 daemon 运行中 |
| **SSH** | ~500ms | ❌ WiFi | 手机 SSHD + Termux |

## 项目结构

```
F:\luoke/
├── phone_hid_dual.py      手机端：USB Gadget 配置（RNDIS + HID）
├── PC/
│   ├── hid_device.py       PC 端：四层传输 + 全键鼠 API
│   └── __init__.py
├── phone/
│   ├── hid_daemon.py       手机端：常驻 daemon（TCP:8023）
│   ├── exec.py             SSH 一次性 Python 执行器
│   └── reset_usb.py        USB 紧急恢复
├── example/
│   ├── rock_hid.py         洛克王国游戏集成封装
│   ├── rock_hid_clicker.py 丢球 CLI 工具
│   ├── 丢球_HID.py         丢球脚本（PC 端）
│   └── 秒丢2.5球.py         高速连丢脚本
├── docs/
│   ├── RNDIS_MODE.md       USB 有线控制通道指南
│   ├── ADB_MODE.md         ADB 触发模式指南
│   └── DUCKSCRIPT.md       DuckyScript 参考（计划中）
├── archive/                历史归档脚本
└── README.md
```

## 快速开始

### 手机端：配置 HID + RNDIS

```bash
# 推送到手机（根据实际情况调整路径）
scp -P <ssh端口> phone_hid_dual.py phone/ <用户>@<手机IP>:~/ -r

# SSH 到手机执行
ssh -p <ssh端口> <用户>@<手机IP> \
  "su -c 'python3 ~/phone_hid_dual.py'"
```

脚本自动完成：
1. 停止 ADB，释放 USB
2. 创建 USB Gadget（HID 键盘 + 鼠标 + RNDIS）
3. 手机 RNDIS 配 IP（192.168.42.2/24）
4. 启动 `hid_daemon.py` 监听 `0.0.0.0:8023`
5. PC 端出现 HID Keyboard、Mouse 和 RNDIS 虚拟网卡

### PC 端：使用 HIDInput

```python
from PC.hid_device import HIDInput

dev = HIDInput()                     # 自动选最快通道：RNDIS > TCP > SSH
dev.mouse.click("left", 175)         # 左键，按住 175ms
dev.mouse.move(100, -50)             # 相对移动 X+100, Y-50
dev.keyboard.tap("A", 40)            # 按 A 40ms
dev.keyboard.tap("LSHIFT", 35)       # 按左 Shift
dev.keyboard.press("W")              # 按住 W
dev.keyboard.release()               # 释放所有键
dev.cmd("throw:175:20:35")           # 原始命令：左键+Shift 序列
```

### 恢复 USB（手机端）

```bash
python3 phone_hid_dual.py restore
# 紧急恢复：python3 phone/reset_usb.py
```

## 配置项

### 手机端环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HID_UDC` | 自动检测 | UDC 名称（如 `a600000.dwc3`） |
| `HID_CONFIGFS_PATH` | `/config/usb_gadget` | ConfigFS 挂载点 |
| `HID_TCP_PORT` | `8023` | Daemon TCP 端口 |
| `HID_GADGET_NAME` | `g1` | Gadget 名称 |
| `HID_VID` | `0x22d9` | 厂商 ID |
| `HID_PID` | `0x2769` | 产品 ID |

### PC 端环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LUOKE_HOST` | `root@<手机>` | SSH 用户@主机 |
| `LUOKE_SSHPORT` | `8022` | SSH 端口 |
| `LUOKE_TCPHOST` | `<手机>` | TCP 连接地址 |
| `LUOKE_TCPPORT` | `8023` | TCP 连接端口 |
| `LUOKE_RNDISHOST` | `192.168.42.2` | RNDIS 手机 IP |
| `LUOKE_PYTHON` | 手机 python 路径 | 手机端 Python 二进制 |
| `LUOKE_HOME` | 手机 home 目录 | 手机端用户目录 |

## 支持的输入

### 鼠标（5 键 + 滚轮）

`left`, `right`, `middle`, `x1`, `x2` · 相对移动 X/Y（−127 ~ +127）· 垂直滚轮

报告格式：`[buttons][X][Y][wheel]`（4 字节）

### 键盘（完整 104 键）

- 字母 A-Z，数字 0-9，功能键 F1-F12
- 修饰键：`LCTRL` `RCTRL` `LSHIFT` `RSHIFT` `LALT` `RALT` `LGUI` `RGUI`
- 别名：`CTRL` `SHIFT` `ALT` `GUI`
- 方向：`UP` `DOWN` `LEFT` `RIGHT`
- 导航：`HOME` `END` `PGUP` `PGDN`
- 编辑：`BKSP` `DEL` `INS` `TAB` `ENTER` `ESC`
- 小键盘：`NUM0`-`NUM9` `NUM_DOT` `NUM_ENTER` `NUM_PLUS` `NUM_MINUS` `NUM_SLASH` `NUM_ASTERISK`
- 锁定：`CAPSLOCK` `NUMLOCK` `SCROLLLOCK`
- 其他：`PAUSE` `PRINTSCREEN` `MENU`

组合键示例：
```python
dev.keyboard.press("LCTRL")    # 按住 Ctrl
dev.keyboard.tap("C", 40)       # 按 C（Ctrl 未松）
dev.keyboard.release()          # 释放所有键
```

## 传输层详解

### RNDIS（首选）
手机在 Gadget 配置中添加 `gsi.rndis` 功能。PC 端出现虚拟以太网卡，TCP:8023 控制命令经 USB 数据线传输。要求内核支持 `gsi.rndis`。

### TCP（WiFi 备用）
手机 daemon 监听 `0.0.0.0:8023`。无 RNDIS 时自动通过 WiFi 连接。

### SSH（兜底）
通过 SSH 管道执行 Python 代码。`phone/exec.py` 解码并运行 base64 编码的 Python 代码，无需 daemon。

## 适配其他手机

1. **找 UDC**：`ls /sys/class/udc/` — 选择非 dummy 的条目
2. **确认 ConfigFS**：`ls /config/usb_gadget/` — 若无则 `mount -t configfs none /config`
3. **确认 RNDIS**：`ls /config/usb_gadget/g1/functions/gsi.rndis` — 不存在则自动降级 TCP

常见 UDC：

| SoC 平台 | UDC 名称 |
|----------|---------|
| 骁龙 865/870/888/8G1/8G2 | `a600000.dwc3` |
| 天玑 Dimensity | `musb-hdrc` / `11200000.usb` |
| 麒麟 Kirin | `ff100000.dwc3` |
| Exynos | `dwc3` |

## 常见问题

| 问题 | 排查方法 |
|------|---------|
| PC 无 HID 设备 | `cat /sys/class/udc/<UDC>/state` — 应为 `configured` |
| RNDIS 网卡未出现 | 内核缺 `gsi.rndis`，自动降级 TCP |
| Daemon 无法启动 | 查看日志：`cat /data/local/tmp/hid_daemon.log` |
| 需恢复 ADB | `python3 phone_hid_dual.py restore` |
| 手动终止 daemon | `touch /data/local/tmp/hid_daemon.quit` |
