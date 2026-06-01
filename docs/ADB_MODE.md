# ADB 触发模式（规划中）

## 说明

通过 ADB 触发 HID 模式，适用于未 Root 或不想用 SSH 的场景。

## 前提

- 手机开启 USB 调试
- PC 有 `adb` 工具
- 手机内置 `hid.keyboard` / `hid.mouse` function（大部分高通 DWC3 平台内置）

## ADB Reverse 端口转发

不需要 Gadget 配置，直接用 ADB 通道转发 TCP：

```bash
# PC 端
adb reverse tcp:8023 tcp:8023

# 然后 PC 端连接 localhost:8023 即可通过 USB 线控制
python -c "from PC.hid_device import HIDInput; d=HIDInput('tcp:127.0.0.1:8023'); d.keyboard.tap('A')"
```

## ADB Shell 启动 HID Gadget

```bash
# 如果手机有 Magisk root
adb shell su -c "python3 /data/data/com.termux/files/home/phone_hid_dual.py"
```
