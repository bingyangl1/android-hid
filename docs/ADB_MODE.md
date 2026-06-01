# ADB 触发模式

## 说明

通过 ADB 触发 HID 模式，适用于不想部署 SSH 或临时控制的场景。

## ADB Reverse 端口转发

不需要修改 Gadget 配置，利用 ADB 已有的 USB 通道转发 TCP：

```bash
# PC 端
adb reverse tcp:8023 tcp:8023

# 然后在 PC 端使用
python -c "
from PC.hid_device import HIDInput
d = HIDInput('tcp:127.0.0.1:8023')
d.keyboard.tap('A')
d.mouse.click('left', 175)
"
```

所有命令走 USB 数据线，不经过 WiFi。

## ADB Shell 启动 HID Gadget（需 Magisk）

```bash
# 手机已 Root + Magisk
adb shell su -c "python3 /data/data/com.termux/files/home/phone_hid_dual.py"
```

## 注意事项

- ADB reverse 仅在该 ADB 会话期间有效，断开后需重设
- 需手机开启 USB 调试
- 需手机内置 `hid.keyboard` / `hid.mouse` function（高通 DWC3 平台默认内置）
- ADB shell 身份（uid=2000）无法直接写 ConfigFS，必须 `su`
