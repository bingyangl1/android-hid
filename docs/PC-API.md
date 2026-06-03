# PC 端 API 文档

## HIDInput

```python
from PC.hid_device import HIDInput

dev = HIDInput(transport_spec=None, show_latency=False)
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `transport_spec` | `str` / `Transport` / `None` | `None` | 传输方式，`None` 自动选择 |
| `show_latency` | `bool` | `False` | 每条命令打印延迟 |

### transport_spec 可选值

| 值 | 说明 |
|------|------|
| `None` | 自动：ADB forward → TCP → SSH |
| `"adb"` | 强制 ADB forward (`localhost:8023`) |
| `"tcp"` | 强制 WiFi TCP (`192.168.5.170:8023`) |
| `"tcp:host:port"` | 自定义 TCP 地址 |
| `"ssh"` | 强制 SSH 隧道 |

### 方法

```python
dev.click(button="left", hold_ms=40)   # 鼠标点击
dev.key(key, hold_ms=40)               # 键盘按键
dev.press(key)                         # 键盘按下
dev.release()                          # 键盘松开
dev.cmd(command)                       # 原始 TCP 命令
dev.batch_throw(n, t1_ms, gap_ms, t2_ms, iv_ms)  # 批量丢球
```

### 延迟统计

```python
dev.latency_stats()
# → {"avg": 4.5, "min": 3.8, "max": 5.2, "p50": 4.5, "p99": 5.2, "count": 100}

dev.latency_str()
# → "avg=4.5ms min=3.8ms max=5.2ms p50=4.5ms p99=5.2ms n=100"
```

---

## HIDMouse

通过 `dev.mouse` 访问。

| 方法 | 参数 | 说明 |
|------|------|------|
| `click(button, hold_ms)` | `left`/`right`/`middle`/`x1`/`x2`, 毫秒 | 点击 |
| `press(button)` | 同上 | 按下不放 |
| `release(button)` | 同上或 `None`(松开当前) | 松开 |
| `move(dx, dy, wheel)` | 相对坐标 (-127~127) | 移动 |

所有方法返回 `self`，支持链式调用。

---

## HIDKeyboard

通过 `dev.keyboard` 访问。

| 方法 | 参数 | 说明 |
|------|------|------|
| `tap(key, hold_ms)` | 键名, 毫秒 | 按一下 |
| `press(key)` | 键名 | 按下不放（追加到 report，支持多键同时） |
| `release(key)` | 键名或 `None` | 释放指定键，不传则全松 |

### 多键同时按

`press` 会追加到 report（最多 6 键），`release("key")` 只移除指定键，其他键保持按下状态：

```python
dev.keyboard.press("LSHIFT")    # Shift 按下
dev.keyboard.press("a")         # A 追加（Shift+A 同时）
dev.keyboard.release("a")       # 只松 A，Shift 还按着
dev.keyboard.release("LSHIFT")  # 松 Shift
```

### 支持的键名

字母 `A`-`Z`，数字 `0`-`9`，功能键 `F1`-`F12`，修饰键 `LCTRL`/`RCTRL`/`LSHIFT`/`RSHIFT`/`LALT`/`RALT`/`LGUI`/`RGUI`（别名 `CTRL`/`SHIFT`/`ALT`/`GUI`），导航键 `UP`/`DOWN`/`LEFT`/`RIGHT`/`HOME`/`END`/`PGUP`/`PGDN`，编辑键 `ENTER`/`ESC`/`BACKSPACE`/`TAB`/`SPACE`/`DELETE`/`INSERT`，锁定键 `CAPSLOCK`/`NUMLOCK`/`SCROLLLOCK`，小键盘 `NUM0`-`NUM9`/`NUM_PLUS`/`NUM_MINUS` 等。

---

## 传输层

### ADBForwardTransport

自动执行 `adb forward tcp:8023 tcp:8023`，连接 `localhost:8023`。需要 ADB 可用（USB 或 WiFi）。

### TCPTransport

直接连接 `192.168.5.170:8023`。需要手机和电脑在同一 WiFi。

### SSHTransport

通过 SSH 到手机，用 `nc localhost 8023` 转发命令。最慢但最可靠。
