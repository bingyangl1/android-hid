# TCP 协议文档

APP 的 TCP 服务器监听 `0.0.0.0:8023`，每行一条命令，返回 `ok` 或 `err:原因`。

## 格式

```
命令:参数1:参数2:...
```

参数可选，用 `:` 分隔。空行和 `#` 开头的行被忽略。

## 命令列表

### 鼠标

| 命令 | 参数 | 示例 | 说明 |
|------|------|------|------|
| `mclick` | `button:hold_ms` | `mclick:left:175` | 点击，按住指定毫秒 |
| `mpress` | `button` | `mpress:right` | 按下不放 |
| `mrelease` | `button`(可选) | `mrelease:left` | 松开指定键，不传则松开全部 |
| `mmove` | `dx:dy:wheel` | `mmove:10:-5:0` | 相对移动，-127~127 |

`button` 可选值：`left`(1), `right`(2), `middle`(4), `x1`(8), `x2`(16)

### 键盘

| 命令 | 参数 | 示例 | 说明 |
|------|------|------|------|
| `ktap` | `key:hold_ms` | `ktap:a:40` | 按一下，按住指定毫秒 |
| `kpress` | `key` | `kpress:lshift` | 按下不放 |
| `krelease` | — | `krelease` | 松开所有键 |

`key` 为 HID usage name（大小写不敏感），如 `a`, `enter`, `f5`, `lshift`, `space`。

### 组合命令

| 命令 | 参数 | 示例 | 说明 |
|------|------|------|------|
| `throw` | `t1:gap:t2` | `throw:175:20:35` | 左键按 t1ms → 松开 → 等 gapms → Shift 按 t2ms → 松开 |
| `bthrow` | `n:t1:gap:t2:iv` | `bthrow:10:175:20:35:500` | 重复 throw n 次，间隔 ivms |

### 其他

| 命令 | 说明 |
|------|------|
| `ping` | 返回 `pong` |
