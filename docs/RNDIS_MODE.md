# USB RNDIS 有线控制通道

## 原理

RNDIS（Remote Network Driver Interface Specification）在 USB 协议之上封装以太网帧，使 USB 数据线变成一根虚拟网线。

```
┌─ PC ─────────────────┐      USB 数据线      ┌─ Phone ──────────────────┐
│                       │ ◄═══════════════════ ► │                          │
│  RNDIS 虚拟网卡       │                        │  usb0 (RNDIS 虚拟网卡)    │
│  192.168.42.1/24     │ ◄──── TCP:8023 ────── ► │  192.168.42.2/24        │
│  hid_device.py        │                        │  hid_daemon.py (:8023)   │
└───────────────────────┘                        └──────────────────────────┘
```

一根 USB 数据线同时走三路数据：
1. HID 键盘报告（手机 → PC）
2. HID 鼠标报告（手机 → PC）
3. RNDIS TCP 控制（双向）

## 前提条件

- 手机内核有 `gsi.rndis` function（高通 DWC3 平台内置）
- 手机已 Root
- USB 数据线连接 PC

## 验证 RNDIS 可用性

```bash
# 手机端检查
ls /config/usb_gadget/g1/functions/gsi.rndis/

# 如果有输出（如 dev_addr host_addr），则内核支持 RNDIS
```

## PC 端网络配置

大多数情况 Windows 会自动为 RNDIS 适配器分配 APIPA 地址。
如果未能自动连通：

```bash
# Windows (管理员 PowerShell)
netsh interface ip set address "以太网 N" static 192.168.42.1 255.255.255.0

# Linux
sudo ip addr add 192.168.42.1/24 dev usb0
sudo ip link set usb0 up
```

## 测试连通性

```bash
ping 192.168.42.2
```
