# 视觉部分开发与验收

只修改 `vision/`。协议以 `docs/03_接口协议.md` 为准；修改协议需先与控制同学协调。

## 模块分工

| 部分 | 文件 | 职责与验收 |
|---|---|---|
| 参数 | config.py | 集中保存曝光、阈值、确认帧数和检测频率 |
| 采集 | camera.py、tools/capture.py | 输出 BGR 图像；实机检查颜色和曝光，采集左右牌及无牌样本 |
| 指示牌 | sign.py、tools/tune_sign.py | 按实地图蓝底白箭头牌的轮廓和箭头尖端判断左/右；同时识别车库旁 P 牌 |
| 颜色 | color_order.py | 从共线候选中选出四个色块，自动适配横排/竖排，允许额外障碍色块和重复颜色 |
| 跨帧状态 | recognition_state.py | 指示牌连续确认及失效；颜色连续确认并锁存至重启 |
| 通信 | protocol.py、uart_link.py | 保持七字节协议；断线限频重连；短写算失败并关闭连接 |
| 显示 | lcd_display.py | 使用 ST7789 SPI 液晶屏持续显示已确认的颜色顺序；无硬件时输出控制台 |
| 调度 | main.py | 按帧计数检测颜色，定频发送；读图失败也继续发送并让旧指示牌失效 |
| 备选测色 | tcs34725.py | 独立传感器驱动，尚未接入主循环，不要将 COLOR_MODE 改为该模式运行 |

## 建议逐步验收

1. 在项目根目录运行无硬件回归测试：`python -m unittest discover -s vision/tests -v`。
2. 在树莓派安装 `requirements.txt` 中的依赖和系统 OpenCV/picamera2；PC 调图需要额外安装 `opencv-python`。
3. 进入 `vision/`，运行 `python tools/capture.py --label left --n 30`，再采集 right、none 和 color。
4. 用 `python tools/tune_sign.py media/capture/left` 检查分割结果，再用 `python tools/replay.py media/capture/left --kind sign` 回放。三类指示牌都要测。
5. 启用 SPI 后先运行 `python tools/test_lcd.py` 检查 ST7789，再用 `python main.py --no-uart` 检查连续确认与显示，最后用 `python main.py --port /dev/serial0` 联调七字节帧。
6. 拿走指示牌、遮住镜头、拔掉串口分别验证：旧转向应清除、心跳应持续、串口恢复后应能重连。

注意：颜色顺序必须按车辆行驶方向确认，重复颜色已经允许。`COLOR_AXIS="auto"` 会适配实地图中横排或竖排的拍摄视角；若相机左右方向与车辆行驶方向相反，只需切换 `COLOR_ORDER_REVERSED`。P 牌在视觉侧编码为 `sign=3`，旧 STM32 固件会安全忽略该保留值，左/右转仍使用原来的 1/2 编码。

主循环是尽力达到 SEND_HZ 的单线程循环，摄像头或 LCD 驱动长时间阻塞时不能保证发送周期。STM32 的超时与转向保护仍由控制模块负责。

## ST7789 接线

默认使用 SPI0 CE0。屏幕资料确认分辨率为 240×320、控制芯片为 ST7789V2、逻辑电压为 3.3V。SCLK=GPIO11，MOSI=GPIO10，CS=GPIO8，DC=GPIO24，RST=GPIO25，BLK=GPIO18。当前 `LCD_ROTATE=1`，以横屏显示。若 BLK 接 GPIO18，安装系统包 `python3-rpi.gpio`，若 BLK 已接 3.3V，可将 `LCD_BACKLIGHT_PIN` 设为 `None`。
