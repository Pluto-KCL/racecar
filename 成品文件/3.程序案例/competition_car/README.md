# 树莓派单机比赛程序

本目录是在没有 STM32 的前提下，根据成品 `code.zip` 中的 `LOBOROBOT.py`、视觉巡线、红外/超声避障和二维码运动示例整理的单机程序。

## 运行

```bash
cd competition_car
python3 main.py --mode line
python3 main.py --mode obstacle
python3 main.py --mode competition
python3 main.py --mode parking
```

先将车架空，确认电机方向，再在低速下调整 `config.py`。`competition` 模式默认执行摄像头黑线循迹、超声波近障停车、彩色箭头牌左右转和四色目标采样。

## 安装

```bash
sudo apt install python3-opencv python3-smbus python3-rpi.gpio
```

摄像头使用 `/dev/video0`。如果树莓派使用 CSI 摄像头而系统没有 V4L2 设备，需要把 `vision.py` 的 `cv2.VideoCapture(0)` 换成成品环境对应的 Picamera2 采集代码。

## 必须实车标定

- `motor_invert` 和电机方向
- `line_gray_threshold`、ROI 和循迹 PID
- 超声波引脚及停车距离
- 指示牌颜色、位置和转弯时间
- 倒车入库的转向与后退时间

程序在摄像头读帧失败、循迹丢失或距离过近时会停止电机。数据手册中的模块并不代表实物一定已安装，未安装的传感器应在 `config.py` 中禁用或改线。
