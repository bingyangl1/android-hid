# USB RNDIS 有线控制通道

## 原理

RNDIS（Remote Network Driver Interface Specification）在 USB 协议之上封装以太网帧。一根 USB 数据线同时传输三路独立数据：

```
┌─ PC ─────────────────┐    USB 数据线     ┌─ Phone ──────────────────┐
│  RNDIS 虚拟网卡       │ ◄═══════════════ ► │  usb0 (RNDIS 虚拟网卡)    │
│  TCP:8023 ────────────┼───────────────────►│  hid_daemon.py (:8023)   │
│  HID Keyboard/Mouse   │ ◄── hidg0/hidg1 ──│  /dev/hidg0 (kbd)        │
└───────────────────────┘                   │  /dev/hidg1 (mouse)       │
                                            └──────────────────────────┘
```

1. HID 键盘报告（手机 → PC，hidg0）
2. HID 鼠标报告（手机 → PC，hidg1）
3. RNDIS TCP 控制（双向，PC ↔ daemon）

## 前提条件

- 手机内核含 `gsi.rndis` function（高通 DWC3 平台内置）
- 手机已 Root
- USB 数据线连接 PC

## 验证 RNDIS 可用性

```bash
# 手机端检查（root）
ls /config/usb_gadget/g1/functions/gsi.rndis/

# 无此目录说明内核不支持 RNDIS，自动降级 WiFi TCP
```

## 操作流程

由 `phone_hid_dual.py` 完成：

1. 重建 USB Gadget，加入 `gsi.rndis` 软链接
2. 设置 MAC：`dev_addr=42:69:69:00:00:02` `host_addr=42:69:69:00:00:01`
3. 绑定 UDC 后自动配置 IP：
   ```
   ip addr add 192.168.42.2/24 dev usb0
   ip link set usb0 up
   ```
4. PC 端自动出现 RNDIS 虚拟网卡
5. `PC/hid_device.py` 的 `RNDISTransport` 自动连接 `192.168.42.2:8023`

## PC 端网络配置

大部分情况 Windows 自动为 RNDIS 适配器分配 APIPA 地址（169.254.x.x）。如未连通：

```bash
# Windows (管理员)
netsh interface ip set address "以太网 N" static 192.168.42.1 255.255.255.0

# Linux
sudo ip addr add 192.168.42.1/24 dev usb0
sudo ip link set usb0 up
```

验证：`ping 192.168.42.2`

## 故障排查

| 现象 | 原因 | 解决 |
|------|------|------|
| 无 rndis 网卡 | 内核不支持 `gsi.rndis` | 自动降级 WiFi，忽略 |
| IP 不通 | PC 未配 IP | `netsh` 手动配置 192.168.42.1/24 |
| daemon 拒绝连接 | daemon 未运行 | 检查 `/data/local/tmp/hid_daemon.log` |
