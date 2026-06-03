# BT HID Bridge

让 Android 手机充当蓝牙键盘+鼠标，通过 TCP 接收命令并模拟 HID 输入。适用于需要硬件级键鼠输入、绕过软件注入检测的场景。

## 架构

```
PC                                          Phone (Android)
──                                          ────────────────
hid_device.py
  │
  ▼ HIDInput()
  ├─ ADBForward ── adb forward tcp:8023 ──→ BT HID Bridge App
  │                                            ├─ BluetoothController (HID)
  ├─ TCPTransport ── WiFi TCP:8023 ─────────→ ├─ TcpServer (:8023)
  │                                            └─ HIDExecutor
  └─ SSHTransport ── SSH tunnel ────────────→      │
                                                   ▼
                                              Bluetooth HID
                                              ├─ Keyboard (HID)
                                              └─ Mouse (HID)
```

传输优先级（自动降级）：

| 层级 | 传输 | 延迟 | 依赖 |
|------|------|------|------|
| 1 | **ADB forward** | ~5ms | ADB 连接（USB/WiFi） |
| 2 | **TCP WiFi** | ~20ms | WiFi |
| 3 | **SSH tunnel** | ~500ms | SSH |

## 快速开始

### 1. 安装 APP

从 [Releases](../../releases) 下载 APK 安装到手机，或自行编译：

```bash
cd android-app && gradle assembleDebug
```

### 2. 配对蓝牙

1. 手机打开 APP，点「启动」
2. 电脑端：设置 → 蓝牙 → 添加蓝牙设备
3. 找到 `BT HID Bridge`，配对
4. APP 显示「已连接: 电脑名」即成功

### 3. 运行脚本

```python
from PC.hid_device import HIDInput

dev = HIDInput()                         # 自动选最快传输
dev = HIDInput("adb")                    # 强制 ADB forward
dev = HIDInput("tcp")                    # 强制 WiFi TCP
dev = HIDInput(show_latency=True)        # 显示每条命令延迟

dev.mouse.click("left", 175)             # 左键点击，按住 175ms
dev.mouse.click("x1", 40)               # 侧键
dev.mouse.move(100, -50)                 # 相对移动
dev.keyboard.tap("LSHIFT", 35)           # 按 Shift 35ms
dev.keyboard.tap("F5")                   # 按 F5
dev.cmd("mclick:left:175")               # 原始命令

print(dev.latency_str())                 # 延迟统计
```

## PC 端 API

### HIDInput

```python
HIDInput(transport_spec=None, show_latency=False)
```

- `transport_spec`: `"adb"` / `"tcp"` / `"ssh"` / `"tcp:host:port"` / `None`(自动)
- `show_latency`: 每条命令打印延迟

### Mouse

| 方法 | 说明 |
|------|------|
| `click(button, hold_ms)` | 点击 (`left`/`right`/`middle`/`x1`/`x2`) |
| `press(button)` | 按下不放 |
| `release(button)` | 松开 |
| `move(dx, dy, wheel)` | 相对移动 |

### Keyboard

| 方法 | 说明 |
|------|------|
| `tap(key, hold_ms)` | 按一下 (`A`-`Z`, `F1`-`F12`, `ENTER`, `LSHIFT` 等) |
| `press(key)` | 按下不放 |
| `release()` | 松开所有键 |

### 延迟统计

```python
dev.latency_stats()   # → {avg, min, max, p50, p99, count}
dev.latency_str()     # → "avg=4.5ms min=3.8ms max=5.2ms ..."
```

## TCP 协议

APP 监听 `0.0.0.0:8023`，命令格式 `command:arg1:arg2:...`，返回 `ok` 或 `err:...`。

| 命令 | 参数 | 说明 |
|------|------|------|
| `mclick` | `button:hold_ms` | 鼠标点击 |
| `mpress` | `button` | 鼠标按下 |
| `mrelease` | `button` | 鼠标松开 |
| `mmove` | `dx:dy:wheel` | 鼠标移动 |
| `ktap` | `key:hold_ms` | 键盘按键 |
| `kpress` | `key` | 键盘按下 |
| `krelease` | — | 键盘松开 |
| `throw` | `t1:gap:t2` | 组合操作：左键→延迟→Shift |
| `bthrow` | `n:t1:gap:t2:iv` | 批量 throw |
| `ping` | — | 返回 `pong` |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LUOKE_HOST` | `root@192.168.5.170` | SSH 地址 |
| `LUOKE_SSHPORT` | `8022` | SSH 端口 |
| `LUOKE_TCPHOST` | `192.168.5.170` | TCP 地址 |
| `LUOKE_TCPPORT` | `8023` | TCP 端口 |
| `LUOKE_ADB` | `adb` | adb 命令路径 |

## 项目结构

```
├── PC/
│   └── hid_device.py          PC端传输层 + 键鼠接口
├── android-app/               Android 蓝牙 HID 桥接 APP
│   └── app/src/main/java/com/hid/btbridge/
│       ├── MainActivity.kt    主界面
│       ├── BluetoothController.kt  蓝牙 HID 控制
│       ├── HidBridgeService.kt     前台服务
│       ├── TcpServer.kt            TCP 服务器
│       ├── HIDExecutor.kt          命令执行
│       ├── CommandParser.kt        命令解析
│       └── reports/                HID 报告描述符
├── example/                   使用示例
└── docs/                      文档
```

## License

MIT
