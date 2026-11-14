# 视觉部分开发与验收

只修改 `vision/`。协议以 `docs/03_接口协议.md` 为准；修改协议需先与控制同学协调。

## 模块分工

| 部分 | 文件 | 职责与验收 |
|---|---|---|
| 参数 | config.py | 集中保存曝光、阈值、确认帧数和检测频率 |
| 采集 | camera.py、tools/capture.py | 输出 BGR 图像；实机检查颜色和曝光，采集左右牌及无牌样本 |
| 指示牌 | sign.py、tools/tune_sign.py | 单帧候选与置信度；当前按牌面所在位置判断左右，尚不识别箭头方向 |
| 颜色 | color_order.py | 四种不同颜色的色块按横向中心排序，方向由 COLOR_ORDER_REVERSED 控制 |
| 跨帧状态 | recognition_state.py | 指示牌连续确认及失效；颜色连续确认并锁存至重启 |
| 通信 | protocol.py、uart_link.py | 保持七字节协议；断线限频重连；短写算失败并关闭连接 |
| 显示 | oled_display.py | 持续显示已确认的颜色顺序；无硬件时输出控制台 |
| 调度 | main.py | 按帧计数检测颜色，定频发送；读图失败也继续发送并让旧指示牌失效 |
| 备选测色 | tcs34725.py | 独立传感器驱动，尚未接入主循环，不要将 COLOR_MODE 改为该模式运行 |

## 建议逐步验收

1. 在项目根目录运行无硬件回归测试：`python -m unittest discover -s vision/tests -v`。
2. 在树莓派安装 `requirements.txt` 中的依赖和系统 OpenCV/picamera2；PC 调图需要额外安装 `opencv-python`。
3. 进入 `vision/`，运行 `python tools/capture.py --label left --n 30`，再采集 right、none 和 color。
4. 用 `python tools/tune_sign.py media/capture/left` 检查分割结果，再用 `python tools/replay.py media/capture/left --kind sign` 回放。三类指示牌都要测。
5. 用 `python main.py --no-uart` 检查连续确认与显示，再用 `python main.py --port /dev/serial0` 联调七字节帧。
6. 拿走指示牌、遮住镜头、拔掉串口分别验证：旧转向应清除、心跳应持续、串口恢复后应能重连。

注意：颜色回放目前只统计是否检测到四块，不能作为顺序准确率。必须人工对照实拍顺序；指示牌箭头识别需要先确认真实牌面样式，再替换单帧算法。

主循环是尽力达到 SEND_HZ 的单线程循环，摄像头或 OLED 驱动长时间阻塞时不能保证发送周期。STM32 的超时与转向保护仍由控制模块负责。
