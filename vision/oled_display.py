"""OLED 显示（0.96" SSD1306，I2C）。

规则要求：颜色顺序必须"在车载屏上持续显示"直到裁判记录。
所以这块屏不是装饰，是 20 分的凭证 —— 字要大、要一直显示、不要闪。

没接屏（在电脑上调参）时自动降级为打印到控制台，不影响其他模块。
"""

import config

try:
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    ssd1306 = None

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


class Display:
    def __init__(self):
        self.dev = None
        self._font = None
        if ssd1306 is not None:
            try:
                serial = i2c(port=config.TCS_I2C_BUS, address=config.OLED_I2C_ADDR)
                self.dev = ssd1306(serial, width=config.OLED_WIDTH, height=config.OLED_HEIGHT)
                self._font = self._load_font(16)
                self.show_lines(["BOOT", "ready"], big=False)
                print("[oled] ssd1306 ready")
            except Exception as e:
                print(f"[oled] init failed, fallback to console: {e}")
                self.dev = None

    def _load_font(self, size):
        for p in _FONT_CANDIDATES:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return ImageFont.load_default()

    def show_lines(self, lines, big=True):
        """lines: 最多 4 行字符串。big=True 时用 16px 粗体。"""
        if self.dev is None:
            print("[oled] " + " | ".join(lines))
            return
        img = Image.new("1", (config.OLED_WIDTH, config.OLED_HEIGHT), 0)
        draw = ImageDraw.Draw(img)
        font = self._load_font(16 if big else 11)
        y = 2
        for line in lines[:4]:
            draw.text((2, y), str(line), font=font, fill=1)
            y += 16 if big else 12
        self.dev.display(img)

    def show_color_order(self, colors, quality=0):
        """颜色顺序是给裁判看的主要信息。128px 宽一行只放得下 R-G-B-Y。"""
        if not colors:
            self.show_lines(["COLOR:", "----", f"q={quality}"])
            return
        short = {"red": "R", "green": "G", "blue": "B", "yellow": "Y"}
        text = "-".join(short.get(c, "?") for c in colors)
        self.show_lines(["COLOR ORDER", text, f"q={quality}"], big=True)

    def show_status(self, state_name, sign=0, quality=0):
        arrow = {0: "--", 1: "LEFT", 2: "RIGHT"}.get(sign, "--")
        self.show_lines([state_name, f"SIGN {arrow}", f"q={quality}"])


__all__ = ["Display"]
