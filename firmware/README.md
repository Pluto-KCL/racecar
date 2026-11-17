# firmware — STM32F103C8T6（C 负责）

## 这个目录怎么用

**不要**把这里的 `app.c` 当 `main.c` 用。正确姿势：

1. STM32CubeMX 新建工程，芯片选 **STM32F103C8Tx**，配好外设（下表）
2. 生成 Keil 或 STM32CubeIDE 工程
3. 把 `Core/Inc/*.h`、`Core/Src/*.c` 复制进生成的工程（同名目录）
4. 打开 CubeMX 生成的 `main.c`，在 `/* USER CODE BEGIN 2 */` 里加：

```c
#include "app.h"
...
  /* USER CODE BEGIN 2 */
  App_Init();
  /* USER CODE END 2 */

  while (1)
  {
    /* USER CODE BEGIN 3 */
    App_Loop();
    /* USER CODE END 3 */
  }
```

这样 CubeMX 重新生成代码时不会覆盖你的逻辑（`USER CODE` 段是保留的）。

## 外设配置（CubeMX 里照这个点）

| 功能 | 引脚 | 配置 |
|---|---|---|
| 循迹 8 路（模拟） | PA0–PA7 | ADC1_IN0–IN7，扫描+连续转换（或逐个轮询） |
| 左电机 PWM | PB6 | TIM4_CH1，PWM Generation，频率 10 kHz |
| 右电机 PWM | PB7 | TIM4_CH2，同上 |
| 左电机方向 | PB12 / PB13 | GPIO 输出（AIN1 / AIN2） |
| 右电机方向 | PB14 / PB15 | GPIO 输出（BIN1 / BIN2） |
| 驱动使能 | PB11 | GPIO 输出（STBY，上电拉高） |
| 超声 TRIG | PB8 | GPIO 输出 |
| 超声 ECHO | PB9 | GPIO 输入（**5V 要分压到 3.3V**） |
| 启动按键 | PB10 | GPIO 输入，内部上拉（按下为低） |
| 串口 | PA9 / PA10 | USART1，115200，8-N-1，**开中断接收** |
| 调试 | PA13 / PA14 | SWD（默认就是） |

时基：SysTick 1 ms。`HAL_Init()` 后 `HAL_Delay()` 可用。

## 模块地图

| 文件 | 职责 | 什么时候改 |
|---|---|---|
| `config.h` | **所有参数**：引脚、PID、速度、阈值、超时 | 调参只改这里 |
| `line_sensor.c` | 8 路 ADC → 加权偏差 `error`（-3500..+3500） | 传感器装反/换阵列时 |
| `pid.c` | 增量式 PID，带积分限幅和输出限幅 | 调 Kp/Ki/Kd |
| `motor.c` | TB6612 方向 + PWM，含死区补偿 | 电机接反、换驱动时 |
| `comm.c` | 串口收帧、校验、超时检测 | 改协议时（先改 docs/03） |
| `ultrasonic.c` | HC-SR04 测距 | 换测距模块时 |
| `state.c` | 状态机：IDLE/RUN/SIGN/COLOR/AVOID/STOP | 加功能时 |
| `app.c` | 初始化 + 主循环，把上面几块串起来 | 少见 |

## 上电顺序（每次都是这个顺序，别乱）

1. 只接 STM32 + ST-Link，烧 `app.c`，看串口有没有打印 `boot`
2. 接 TB6612 和电机（**先架空车轮**），按按键，轮子应该正转 2 秒反转 2 秒
3. 接循迹阵列，手动把黑线在传感器下面移动，串口看 `error` 从 -3500 变到 +3500
4. 接树莓派，`python tools/view_frames.py` 确认收到帧
5. 落地跑直线

## 三条安全保护（`state.c` 里已实现，别删）

- **串口 200 ms 无帧** → 不再执行 `sign` 转向，只循迹
- **超声 < 15 cm** → 停车（避障阶段才启用）
- **上电先 IDLE**，必须按键才进 RUN（防止一上电就冲出去）

## 编译

- **Keil MDK**：`Options → C/C++ → Include Paths` 加 `Core/Inc`；勾 `MicroLIB`
- **STM32CubeIDE**：生成的工程直接编译，把 `.c` 加进 `Core/Src` 即可
- 烧录：ST-Link V2，SWD 4 线（3.3V / GND / SWDIO / SWCLK）
