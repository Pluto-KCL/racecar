"""所有可调参数集中在这里 —— 调参只改这个文件。

约定：
  * 带 TUNABLE 的，是比赛现场允许调的（只有 3 个：EXPOSURE_US / SPEED_HINT / SIGN_MIN_QUALITY）
  * 其他参数只在实验室里改，改完要 commit，写清"改了什么、10 次成功几次"
"""

# ---------- 串口 ----------
SERIAL_PORT = "/dev/serial0"   # 树莓派 GPIO14/15；用 USB-TTL 时改 /dev/ttyUSB0
SERIAL_BAUD = 115200
SEND_HZ = 25                   # 目标帧率，20~30 之间

# ---------- 摄像头 ----------
CAM_WIDTH = 640
CAM_HEIGHT = 480
CAM_FORMAT = "RGB888"
EXPOSURE_US = 8000             # TUNABLE：光线暗就调大，过曝就调小

# 循迹看地面；实地图中的交通牌和车库牌都立在地面边缘，不能只看图像上半部。
ROAD_ROI = (0, 240, 640, 480)      # (x1, y1, x2, y2)
SIGN_ROI = (0, 0, 640, 430)

# ---------- 指示牌（左/右/车库） ----------
# 实地图使用蓝底白色圆形左/右转牌，车库旁另有蓝底白色 P 牌。
# 只分割蓝色，再在蓝色轮廓内部检查白色箭头/P，避免把四色方块误报成转向牌。
SIGN_BLUE_HSV = ((90, 65, 35), (140, 255, 255))
SIGN_WHITE_MIN_V = 150
SIGN_WHITE_MAX_S = 95
SIGN_MIN_AREA = 300            # 640x480 图像中远处牌的最小面积
SIGN_MIN_CIRCULARITY = 0.55    # 圆形箭头牌下限；方形 P 牌走另一条判断
SIGN_MIN_WHITE_RATIO = 0.001       # 远处牌在 640x480 中的白箭头可能只有几像素
SIGN_MIN_WHITE_PIXELS = 4
SIGN_MIN_QUALITY = 40          # TUNABLE：低于这个置信度不转向
SIGN_CONFIRM_FRAMES = 3        # 连续几帧同向才算数（与 STM32 的保护对应）
SIGN_LOST_FRAMES = 3           # 连续丢失/低置信帧达到此数后清除旧指示牌
SIGN_ARROW_DEADZONE = 0.04     # 箭头白色像素质心离中心太近时不判方向

# ---------- 颜色顺序 ----------
# 方案 1（主）：摄像头看 4 个色块，按出现顺序编码
# 方案 2（备）：TCS34725 贴近测单块颜色（更准，但要求车停在每个块前）
COLOR_MODE = "camera"          # "camera" | "tcs34725"
COLOR_MIN_AREA = 50            # 640x480 远处色块可能只有约 10x10 像素
COLOR_DETECT_EVERY = 2         # 按帧计数检测，不能用时间戳奇偶代替
COLOR_CONFIRM_FRAMES = 3       # 连续检测到相同顺序后锁存，供裁判记录
COLOR_MIN_QUALITY = 30
# 实地图的色块可能因相机视角呈横排或竖排；检测器自动沿四块的长轴排序。
# 该开关只负责“相机排序方向”到“车辆行驶方向”的映射，装车后按一次实跑结果校准。
COLOR_ORDER_REVERSED = False
COLOR_AXIS = "auto"            # "auto" | "x" | "y"
COLOR_MAX_LINE_RESIDUAL = 0.16 # 归一化到图像短边的共线残差上限
COLOR_MIN_AXIS_SPREAD = 0.08   # 四块在排序轴上的最小跨度（归一化）
LCD_REFRESH_HZ = 5

# HSV 阈值（OpenCV 里 H 是 0~179）。实验室里用 tools/tune_color.py 现场取。
COLOR_HSV = {
    "red":    [((0, 120, 70),   (10, 255, 255)), ((170, 120, 70), (179, 255, 255))],
    "green":  [((40, 80, 60),   (85, 255, 255))],
    "blue":   [((90, 100, 60),  (130, 255, 255))],
    "yellow": [((20, 120, 90),  (38, 255, 255))],
}

# ---------- TCS34725（备选方案）----------
TCS_I2C_BUS = 1
TCS_I2C_ADDR = 0x29
TCS_INTEGRATION_MS = 100       # 积分时间，越长越准但越慢
TCS_GAIN = 4                   # 1 / 4 / 16 / 60

# ---------- ST7789 SPI LCD ----------
LCD_SPI_PORT = 0
LCD_SPI_DEVICE = 0             # CE0 / GPIO8
# 16 MHz leaves enough timing margin on long Dupont wires.  Increase only
# after the panel is known to render reliably.
LCD_SPI_SPEED_HZ = 16_000_000
LCD_WIDTH = 240                # 屏幕资料：240(RGB) x 320
LCD_HEIGHT = 320
LCD_ROTATE = 1                 # 1=顺时针 90°，横屏显示；可改为 0/2/3
LCD_DC_PIN = 24                # BCM GPIO24
LCD_RESET_PIN = 25             # BCM GPIO25
LCD_BACKLIGHT_PIN = 18         # BCM GPIO18；若 BLK 已接 3.3V，改为 None
# Most 240x320 modules use a zero origin.  Some boards reserve a controller
# margin; these two values can be adjusted without changing lcd_display.py.
LCD_X_OFFSET = 0
LCD_Y_OFFSET = 0
LCD_BGR = False                # 面板颜色反向时改为 True
LCD_BIG_FONT_SIZE = 28
LCD_SMALL_FONT_SIZE = 20

# ---------- 调试 ----------
SAVE_DEBUG_FRAMES = False      # True 时把每帧存到 media/debug/，比赛时关掉
LOG_DIR = "logs"
