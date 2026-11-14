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

# 只处理图像下半部分（循迹看地面），省 CPU。指示牌在上半部分，用另一块 ROI。
ROAD_ROI = (0, 240, 640, 480)      # (x1, y1, x2, y2)
SIGN_ROI = (0, 0, 640, 240)

# ---------- 指示牌（左/右）----------
# 牌面是菱形 + 箭头。先用最笨但可靠的办法：在 SIGN_ROI 里找"非背景色的实心区域"，
# 再看它偏向画面左侧还是右侧。
SIGN_MIN_AREA = 1200           # 最小轮廓面积（像素），太小当噪声
SIGN_MIN_QUALITY = 40          # TUNABLE：低于这个置信度不转向
SIGN_CONFIRM_FRAMES = 3        # 连续几帧同向才算数（与 STM32 的保护对应）
SIGN_LOST_FRAMES = 3           # 连续丢失/低置信帧达到此数后清除旧指示牌

# ---------- 颜色顺序 ----------
# 方案 1（主）：摄像头看 4 个色块，按出现顺序编码
# 方案 2（备）：TCS34725 贴近测单块颜色（更准，但要求车停在每个块前）
COLOR_MODE = "camera"          # "camera" | "tcs34725"
COLOR_MIN_AREA = 800           # 单个色块最小面积
COLOR_DETECT_EVERY = 2         # 按帧计数检测，不能用时间戳奇偶代替
COLOR_CONFIRM_FRAMES = 3       # 连续检测到相同顺序后锁存，供裁判记录
COLOR_MIN_QUALITY = 30
COLOR_ORDER_REVERSED = False
OLED_REFRESH_HZ = 5

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

# ---------- OLED ----------
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_I2C_ADDR = 0x3C

# ---------- 调试 ----------
SAVE_DEBUG_FRAMES = False      # True 时把每帧存到 media/debug/，比赛时关掉
LOG_DIR = "logs"
