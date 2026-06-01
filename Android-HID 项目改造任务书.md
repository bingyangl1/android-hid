# Android\-HID 项目改造任务书

## 文档信息

|项目|内容|
|---|---|
|项目名称|Android\-HID 功能增强与体验优化|
|基于版本|bingyangl1/android\-hid dev 分支|
|参考项目|androidmalware/android\_hid|
|交付团队|opencode|
|文档版本|v1\.0|
|更新日期|2026\-06\-02|

---

## 一、改造目标

### 1\.1 核心目标

将当前 **仅支持 Root 用户、仅能控制 PC、游戏专用** 的小众工具，改造为：

- ✅ **支持免 Root 使用**（ADB 触发模式）

- ✅ **支持 OTG 直连**（控制任意设备：手机 / 平板 / PC / 电视）

- ✅ **支持标准 DuckyScript**（接入成熟自动化生态）

- ✅ **通用 HID 输入平台**（不再局限于游戏场景）

### 1\.2 用户体验目标

- 普通用户无需 Root 即可使用（降低 90% 使用门槛）

- 无需 PC 端软件，手机可独立运行

- 即插即用，兼容所有支持 USB HID 的设备

---

## 二、改造任务清单（按优先级）

---

### 🎯 P0 最高优先级：免 Root ADB 触发模式

#### 任务编号：TASK\-001

#### 任务名称：实现 ADB 触发免 Root 模式

**任务描述**：
参考 androidmalware/android\_hid 的实现，增加通过 ADB 触发 HID 模式的能力，用户不需要永久 Root 手机。

**技术要点**：

1. 检测当前执行身份，如果是 `adb shell` 身份（uid=2000），跳过 su 权限检查

2. 验证 `adb shell` 身份是否具备 ConfigFS 操作权限

3. 修改 `phone_hid_dual.py` 权限检查逻辑

4. 增加免 Root 模式的引导提示

**代码修改范围**：

- `phone_hid_dual.py` \- 权限检测模块

- 新增 `adb_enable_hid.sh` \- 一键触发脚本

**验收标准**：
✅ **AC1：权限检测正确**

- 未 Root 手机，通过 `adb shell python3 phone_hid_dual.py` 可正常执行

- 不弹出 "需要 Root 权限" 错误提示

- ConfigFS 配置成功，`/dev/hidg0` `/dev/hidg1` 设备节点创建成功

✅ **AC2：功能完整性**

- 免 Root 模式下键盘输入功能正常

- 免 Root 模式下鼠标移动 / 点击功能正常

- USB ACM / TCP 传输层正常工作

✅ **AC3：用户引导**

- 直接在手机 Termux 执行时，检测到无 Root 时，给出明确引导：

    ```Plain Text
    检测到未获取Root权限
    请将手机连接电脑，执行：
    adb shell python3 /data/data/com.termux/files/home/phone_hid_dual.py
    ```

✅ **AC4：兼容性**

- 支持 Android 10 \- Android 14

- 支持高通 / 联发科主流芯片

- 主流品牌（小米 / OPPO / 一加 / 三星）原厂内核可正常工作

---

### 🎯 P0 最高优先级：OTG 直连目标设备模式

#### 任务编号：TASK\-002

#### 任务名称：实现 OTG 直连独立运行模式

**任务描述**：
增加手机通过 OTG 线缆直接连接并控制其他设备（安卓 / PC / 电视 / 平板）的能力，不需要 PC 端软件，手机独立运行。

**技术要点**：

1. 实现 USB 角色切换（Device 模式 → 模拟 HID 设备）

2. 开发手机端简易控制界面（命令行即可）

3. 支持手机触摸板 → 鼠标移动映射

4. 支持手机物理键盘 / 软键盘输入转发

**代码修改范围**：

- 新增 `otg_controller.py` \- OTG 模式控制器

- 修改 `phone_hid_dual.py` \- 增加 OTG 模式启动参数

- 新增 `keymap_android.py` \- 安卓设备特殊键映射

**验收标准**：
✅ **AC1：设备连接**

- 手机通过 OTG 线连接 PC，PC 端识别出 "USB HID Keyboard" 和 "USB HID Mouse"

- 手机通过 OTG 线连接安卓设备，安卓端识别外接键盘鼠标

- 无需在目标设备安装任何软件

✅ **AC2：鼠标控制**

- 手机屏幕触摸区域可作为触摸板控制鼠标移动

- 支持左键 / 右键点击

- 支持双指滚动

✅ **AC3：键盘输入**

- 手机输入法输入的文字可发送到目标设备

- 支持特殊按键（ESC/Enter/F1\-F12 等）

- 支持组合键（Ctrl\+C/Ctrl\+V/Alt\+Tab 等）

✅ **AC4：独立运行**

- 不需要连接电脑

- 不需要启动 hid\_daemon 的 TCP/USB ACM 传输层

- 手机端可完全独立操作

---

### 🎯 P1 高优先级：DuckyScript 脚本引擎支持

#### 任务编号：TASK\-003

#### 任务名称：实现标准 DuckyScript 解析与执行引擎

**任务描述**：
支持 USB Rubber Ducky 标准的 DuckyScript 语法，复用社区海量现有 payload，实现强大的自动化能力。

**技术要点**：

1. 实现完整的 DuckyScript 语法解析器

2. 支持所有标准命令：STRING/DELAY/GUI/ALT/CTRL/SHIFT 等

3. 支持脚本文件批量执行

4. 支持实时显示执行进度

**代码修改范围**：

- 新增 `ducky_parser.py` \- DuckyScript 解析器

- 在 `hid_device.py` 中集成执行引擎

- 新增 `scripts/` 目录存放示例脚本

**验收标准**：
✅ **AC1：语法支持完整**

- 支持所有标准 DuckyScript 命令：

    - `STRING text` \- 输入文本

    - `DELAY ms` \- 延时

    - `GUI` / `WINDOWS` \- Win 键

    - `CTRL` / `SHIFT` / `ALT` \- 修饰键

    - `ENTER` / `ESC` / `TAB` \- 特殊键

    - `F1-F12` \- 功能键

    - `UP` / `DOWN` / `LEFT` / `RIGHT` \- 方向键

✅ **AC2：脚本执行正确**

```duckyscript
DELAY 1000
GUI r
DELAY 500
STRING notepad
ENTER
DELAY 500
STRING Hello World from DuckyScript!
```

执行以上脚本可正确打开记事本并输入文字

✅ **AC3：错误处理**

- 语法错误给出明确行号和错误信息

- 支持执行中断（Ctrl\+C）

- 执行完成给出统计报告

✅ **AC4：兼容性**

- 可直接执行互联网上公开的 DuckyScript 脚本无需修改

- 支持 UTF\-8 中文输入

---

### 🎯 P1 高优先级：目标设备兼容性增强

#### 任务编号：TASK\-004

#### 任务名称：多目标设备适配与自动检测

**任务描述**：
优化 HID 报告描述符，增强对不同类型目标设备的兼容性，特别是安卓设备的特殊按键支持。

**技术要点**：

1. 优化 HID 报告描述符，兼容 BIOS/UEFI/ 安卓 /iOS

2. 增加安卓特殊按键映射（HOME/BACK/MENU/VOLUME 等）

3. 实现目标设备类型自动检测与映射表自动切换

4. 增加多媒体按键支持（播放 / 暂停 / 音量等）

**代码修改范围**：

- `phone_hid_dual.py` \- HID 报告描述符

- 新增 `keymap_multimedia.py` \- 多媒体键映射

- 新增 `keymap_android_special.py` \- 安卓特殊键

**验收标准**：
✅ **AC1：全场景兼容**

- PC BIOS/UEFI 界面可正常操作

- Windows/macOS/Linux 桌面正常

- 安卓手机 / 平板正常

- 智能电视 / 盒子正常

✅ **AC2：安卓特殊按键**

- 可模拟安卓 HOME 键

- 可模拟安卓 BACK 键

- 可模拟安卓 MENU 键

- 可模拟音量加减 / 电源键

✅ **AC3：多媒体按键**

- 播放 / 暂停

- 上一曲 / 下一曲

- 音量加 / 减 / 静音

✅ **AC4：自动检测**

- 自动识别目标设备类型

- 自动切换最佳按键映射表

---

### 🎯 P2 中优先级：无守护进程轻量模式

#### 任务编号：TASK\-005

#### 任务名称：实现直接写设备的轻量执行模式

**任务描述**：
增加轻量执行模式，绕过 hid\_daemon，直接写入 /dev/hidg 设备节点，降低资源占用，适合简单脚本。

**技术要点**：

1. 实现直接写 `/dev/hidg0` `/dev/hidg1` 的底层 API

2. 支持单次执行，不需要后台常驻进程

3. 作为 daemon 模式的备用方案

**代码修改范围**：

- `hid_device.py` \- 增加 DirectWriter 类

- 新增 `direct_hid.py` \- 轻量模式入口

**验收标准**：
✅ **AC1：功能等价**

- 轻量模式与 daemon 模式按键输入效果完全一致

- 鼠标移动 / 点击效果完全一致

✅ **AC2：资源占用**

- 无后台进程常驻

- 执行完成立即退出，无残留

- 内存占用 \< 10MB

✅ **AC3：错误恢复**

- daemon 崩溃时可自动降级到直写模式

- 提供手动切换开关

---

### 🎯 P2 中优先级：安卓控制安卓场景优化

#### 任务编号：TASK\-006

#### 任务名称：安卓设备间控制专项优化

**任务描述**：
针对 "安卓手机控制另一台安卓手机" 场景进行专项优化，实现解锁、自动化操作等功能。

**技术要点**：

1. 安卓 PIN 码 / 图案解锁自动化

2. 安卓系统 UI 操作优化

3. 多设备群控基础框架

**验收标准**：
✅ **AC1：解锁功能**

- 支持 4 位 / 6 位 PIN 码自动输入解锁

- 支持图案解锁模拟

✅ **AC2：系统操作**

- 一键返回桌面

- 一键打开最近任务

- 一键下拉通知栏

✅ **AC3：群控基础**

- 可配置多设备参数

- 支持批量执行相同操作

---

## 三、整体验收标准

### 3\.1 功能验收

|功能模块|验收通过标准|
|---|---|
|免 Root 模式|未 Root 手机通过 ADB 触发可正常使用全部功能|
|OTG 直连模式|手机 OTG 连接任意设备可正常控制键鼠|
|DuckyScript|标准脚本 100% 正确执行|
|多设备兼容|PC / 安卓 / 电视均正常工作|

### 3\.2 兼容性验收

- ✅ Android 版本：10, 11, 12, 13, 14

- ✅ 芯片平台：高通骁龙 865/870/888/8Gen1/8Gen2，联发科天玑系列

- ✅ 设备品牌：小米、OPPO、vivo、一加、三星、谷歌 Pixel

- ✅ 目标系统：Windows 10/11, macOS, Linux, Android, iOS/iPadOS

### 3\.3 性能验收

- ✅ 按键延迟 \< 10ms

- ✅ 鼠标移动无明显卡顿

- ✅ 连续输入 1 小时无断开、无丢键

- ✅ 热插拔 50 次无异常

### 3\.4 代码质量验收

- ✅ 代码注释完整，关键逻辑有说明

- ✅ 无硬编码，配置项集中管理

- ✅ 错误处理完善，异常有明确提示

- ✅ 向后兼容原有 Root 模式全部功能

---

## 四、交付物要求

### 4\.1 代码交付

```Plain Text
android-hid/
├── phone_hid_dual.py          # 已修改，支持免Root
├── hid_device.py              # 已修改，集成DuckyScript
├── otg_controller.py          # 新增，OTG模式控制器
├── ducky_parser.py            # 新增，DuckyScript解析器
├── direct_hid.py              # 新增，轻量模式
├── adb_enable_hid.sh          # 新增，免Root一键脚本
├── keymap/
│   ├── __init__.py
│   ├── standard.py
│   ├── android.py
│   └── multimedia.py
├── scripts/                   # DuckyScript示例
│   ├── demo_notepad.txt
│   ├── android_unlock.txt
│   └── README.md
└── docs/
    ├── 免Root使用指南.md
    ├── OTG模式使用指南.md
    └── DuckyScript语法参考.md
```

### 4\.2 文档交付

1. 《免 Root 模式使用指南》

2. 《OTG 直连模式使用指南》

3. 《DuckyScript 开发手册》

4. 《常见问题排查手册》

5. 更新主 \[README\.md\]\(README\.md\)，包含新功能说明

---

## 五、里程碑计划

|里程碑|内容|完成时间|
|---|---|---|
|M1|TASK\-001 免 Root 模式完成|第 1 周|
|M2|TASK\-002 OTG 直连模式完成|第 2 周|
|M3|TASK\-003 DuckyScript 引擎完成|第 2\-3 周|
|M4|TASK\-004\~006 优化功能完成|第 3\-4 周|
|M5|整体测试、文档完善、交付|第 4 周|

---

## 六、注意事项

1. **向后兼容**：所有改造必须不破坏原有 Root 模式、PC 控制游戏的核心功能

2. **内核兼容**：尽量不依赖特定内核配置，最大化兼容性

3. **错误处理**：各种异常场景要有明确的用户提示和恢复方案

4. **安全提示**：文档中需明确说明 HID 技术的安全风险，仅限合法用途

> （注：文档部分内容可能由 AI 生成）
