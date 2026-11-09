# racecar — 星火杯赛题二（智能车）

> 3 人 / 20 天 / 零经验。**先让车稳定循迹，再加识别功能。**
> 计划见 [docs/01_计划_执行版.md](docs/01_计划_执行版.md)，采购见 [docs/02_采购清单_采购版.md](docs/02_采购清单_采购版.md)。

## 硬件架构（已定）

```
前视 CSI 摄像头 ──> 树莓派 4B 2GB ──── 指示牌识别 / 颜色顺序 / OLED 显示
                        │ UART 3 线 (3.3V, 115200)
                        ▼
8 路红外循迹阵列 ──> STM32F103C8T6 ──── 循迹 PID / PWM / 电机 / HC-SR04 / 状态机
                        │
                    TB6612 × 1 ──> TT 电机 ×2
```

**分工边界（最重要的一条）**：树莓派只发"我看到什么"，STM32 决定"车怎么动"。
视觉板拔掉，车必须能安全减速/停车。

## 谁改哪里（防止互相覆盖）

| 人 | 只动这些 | 绝对别动 |
|---|---|---|
| **A 机械/电源** | `hardware/`、`docs/04_接线与验收.md`、`logs/` | 不提交代码 |
| **B 视觉** | `vision/**`、`docs/03_接口协议.md`（改前先在群里说） | 不碰 `firmware/` |
| **C 控制** | `firmware/**`、`tools/` | 不碰 `vision/` |

三个人共用 `docs/` 和 `logs/`，但**同一个文件不要两个人同时改**。

## 目录地图

```
racecar/
├── docs/            计划、采购、接口协议、接线、日志模板（一切"约定"都在这）
├── vision/          B：树莓派 Python，取图 → 识别 → 打包 → 串口发
│   └── tools/       离线调参/回放/存图（不装车也能干）
├── firmware/        C：STM32 C 代码，收帧 → 状态机 → PID → PWM
├── tools/           PC 端：看帧、模拟视觉板、画曲线
├── logs/            每次调车 5 行记录 + 数据
└── media/           照片、视频（大文件，别塞进 git）
```

## 5 分钟跑起来

### 树莓派（B）

```bash
cd vision
python3 -m pip install -r requirements.txt   # picamera2 用 apt: sudo apt install -y python3-picamera2
python3 tools/capture.py                     # 先只验证摄像头能存图
python3 main.py                              # 跑主循环
```

### STM32（C）

1. CubeMX 生成工程（F103C8T6，USART1 115200、TIM1/TIM3 PWM、ADC1 8 通道、I2C1）
2. 把 `firmware/Core/Inc|Src` 里的文件加进工程
3. 先只烧 `main.c` 里的"电机正反转自检"，确认轮子转，再接循迹
4. 编译烧录用 Keil / STM32CubeIDE 都行，见 [firmware/README.md](firmware/README.md)

### 两边联调（C + B）

```bash
python tools/view_frames.py --port COM5      # 先确认帧格式对得上
python tools/simulate_vision.py --port COM5  # 没接树莓派时，用 PC 假装是视觉板
```

## 三条铁律

1. **所有可调参数只在两个文件里**：`vision/config.py`、`firmware/Core/Inc/config.h`。散落在别处的常量，三天后没人记得为什么是那个数。
2. **接口只在一处定义**：[docs/03_接口协议.md](docs/03_接口协议.md)。改协议 = 改这个文件 + 同时改两边 + 群里说一声。
3. **每次只改一个变量**（速度 / 阈值 / 传感器高度 / PID 之一），改完跑 10 次统计成功率。

## 交付节点 ↔ git tag

| 日期 | 必须能演示 | tag |
|---|---|---|
| 11-11 | 电源稳定、电机正反转、摄像头出图、循迹阵列有输出 | `v0.1-上电` |
| 11-14 | 直线循迹 1 m，10 次 ≥ 6 次 | `v0.2-直线` |
| 11-18 | 过一个 90° 弯；颜色在 OLED 显示 | `v0.3-过弯` |
| 11-21 | 连续两弯；指示牌离线准确率 ≥ 80% | `v0.4-指示牌` |
| 11-25 | 循迹+颜色+指示牌 连跑 5 次 ≥ 3 次 | `v0.5-串通` |
| 11-27 | 参数固化、加固接线、备件齐 | `v1.0-封存` |
| 11-28 | **只用封存版本**跑完整流程 | 不再打 tag |

**11-27 之后不再改核心代码。** 现场只允许调 `config.py` / `config.h` 里标了 `TUNABLE` 的 3 个参数。

## 每天收工前

```bash
git add -A && git commit -m "直线10次6次通过，P=8 D=0.5 速度40%"
git tag v0.2-直线          # 只有到交付节点才打
```
