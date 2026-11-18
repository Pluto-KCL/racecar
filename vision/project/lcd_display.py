"""ST7789 SPI 液晶显示。

默认按 320x240、SPI0 CE0、DC=GPIO24、RST=GPIO25 配置。
具体屏幕的分辨率、旋转方向和 BLK 接法以 PCB 丝印为准，参数集中在 config.py。

没有安装 luma.lcd 或屏幕初始化失败时，自动退回控制台输出。
"""

import config

try:
    from luma.core.interface.serial import spi
    from luma.lcd.device import st7789
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    spi = None
    st7789 = None


_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


class Display:
    def __init__(self):
        self.dev = None
        self._gpio = None
        self._font_cache = {}

        if st7789 is None:
            print("[lcd] luma.lcd/Pillow unavailable, fallback to console")
            return

        try:
            serial = spi(
                port=config.LCD_SPI_PORT,
                device=config.LCD_SPI_DEVICE,
                gpio_DC=config.LCD_DC_PIN,
                gpio_RST=config.LCD_RESET_PIN,
                bus_speed_hz=config.LCD_SPI_SPEED_HZ,
            )
            self.dev = st7789(
                serial,
                width=config.LCD_WIDTH,
                height=config.LCD_HEIGHT,
                rotate=config.LCD_ROTATE,
            )
            self._set_backlight(True)
            self.show_lines(["BOOT", "READY"], big=True)
            print(f"[lcd] ST7789 ready: {config.LCD_WIDTH}x{config.LCD_HEIGHT}")
        except Exception as exc:
            self.dev = None
            self._set_backlight(False)
            print(f"[lcd] init failed, fallback to console: {exc}")

    def _set_backlight(self, enabled):
        """BLK 可接 GPIO，也可以在 config.py 设为 None 后直接接 3.3V。"""
        pin = config.LCD_BACKLIGHT_PIN
        if pin is None:
            return
        try:
            import RPi.GPIO as GPIO
            if self._gpio is None:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
                self._gpio = GPIO
            self._gpio.output(pin, GPIO.HIGH if enabled else GPIO.LOW)
        except Exception as exc:
            if enabled:
                print(f"[lcd] backlight control unavailable, connect BLK to 3.3V: {exc}")

    def _load_font(self, size):
        if size in self._font_cache:
            return self._font_cache[size]
        for path in _FONT_CANDIDATES:
            try:
                font = ImageFont.truetype(path, size)
                self._font_cache[size] = font
                return font
            except Exception:
                continue
        font = ImageFont.load_default()
        self._font_cache[size] = font
        return font

    def show_lines(self, lines, big=True):
        """显示最多四行英文或字母数字文本。"""
        lines = [str(line) for line in lines[:4]]
        if self.dev is None:
            print("[lcd] " + " | ".join(lines))
            return

        # luma 在旋转后会交换逻辑宽高，绘图画布使用设备的实际逻辑尺寸。
        width, height = self.dev.width, self.dev.height
        image = Image.new("RGB", (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        font_size = config.LCD_BIG_FONT_SIZE if big else config.LCD_SMALL_FONT_SIZE
        font = self._load_font(font_size)
        line_height = font_size + 8
        y = max(2, (height - line_height * len(lines)) // 2)

        for line in lines:
            box = draw.textbbox((0, 0), line, font=font)
            x = max(2, (width - (box[2] - box[0])) // 2)
            draw.text((x, y), line, font=font, fill=(255, 255, 255))
            y += line_height

        self.dev.display(image)

    def show_color_order(self, colors, quality=0):
        """持续显示颜色顺序，重复颜色也按位置保留。"""
        if not colors:
            self.show_lines(["COLOR", "----", f"Q {quality}"], big=True)
            return
        short = {"red": "R", "green": "G", "blue": "B", "yellow": "Y"}
        text = "-".join(short.get(color, "?") for color in colors)
        self.show_lines(["COLOR ORDER", text, f"Q {quality}"], big=True)

    def show_status(self, state_name, sign=0, quality=0):
        arrow = {0: "--", 1: "LEFT", 2: "RIGHT", 3: "PARK"}.get(sign, "--")
        self.show_lines([state_name, f"SIGN {arrow}", f"Q {quality}"], big=True)

    def close(self):
        self._set_backlight(False)
        self.dev = None


__all__ = ["Display"]
