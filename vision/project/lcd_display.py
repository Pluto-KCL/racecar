"""ST7789 SPI 液晶显示。

本项目使用的是常见的 240x320 ST7789。``luma.lcd`` 自带的 ``st7789``
类面向 240x240 屏幕，初始化时还使用 18-bit 色彩格式；部分 240x320
屏幕会因此只亮背光而不显示图像。这里保留 luma 的 SPI/GPIO 接口，但使用
适用于 240x320 的初始化序列和 RGB565 像素传输。

没有安装 luma.core/Pillow 或屏幕初始化失败时，自动退回控制台输出。
"""

import config
import time

try:
    from luma.core.interface.serial import spi
    from luma.core.device import device as _LumaDevice
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    spi = None
    _LumaDevice = None

    # Keep the names available to the fallback path.  This also makes the
    # module importable on a development PC without Pillow/luma installed.
    Image = ImageDraw = ImageFont = None


_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _rgb565_bytes(image):
    """Convert an RGB Pillow image to the big-endian RGB565 byte stream."""
    image = image.convert("RGB")

    # numpy is already a project dependency on the Pi and keeps a full-frame
    # refresh fast enough for the 5 Hz LCD update.  Keep a small pure-Python
    # fallback so the conversion remains testable on a minimal installation.
    try:
        import numpy as np

        pixels = np.asarray(image, dtype=np.uint16)
        value = ((pixels[:, :, 0] & 0xF8) << 8) \
            | ((pixels[:, :, 1] & 0xFC) << 3) \
            | (pixels[:, :, 2] >> 3)
        return value.byteswap().tobytes()
    except ImportError:
        raw = bytearray(image.width * image.height * 2)
        i = 0
        for red, green, blue in image.getdata():
            value = ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)
            raw[i] = value >> 8
            raw[i + 1] = value & 0xFF
            i += 2
        return bytes(raw)


if _LumaDevice is not None:
    class _ST7789Device(_LumaDevice):
        """Minimal 240x320 ST7789 driver built on luma's SPI interface."""

        _SWRESET = 0x01
        _SLPOUT = 0x11
        _NORON = 0x13
        _INVON = 0x21
        _DISPON = 0x29
        _CASET = 0x2A
        _RASET = 0x2B
        _RAMWR = 0x2C
        _MADCTL = 0x36
        _COLMOD = 0x3A

        def __init__(self, serial_interface, width, height, rotate,
                     x_offset=0, y_offset=0, bgr=False):
            super().__init__(serial_interface=serial_interface)
            self.capabilities(width, height, rotate, mode="RGB")
            self._x_offset = int(x_offset)
            self._y_offset = int(y_offset)

            # The image is rotated by luma's preprocess() before it reaches
            # the controller.  Keep the controller in its native 240x320
            # orientation and only add BGR when a panel requires it.
            madctl = 0x08 if bgr else 0x00
            self._command(self._SWRESET)
            time.sleep(0.150)
            self._command(self._SLPOUT)
            time.sleep(0.120)
            self._command(self._COLMOD, 0x55)  # RGB565, 16 bits/pixel
            self._command(self._MADCTL, madctl)

            # ST7789 power, porch, frame-rate and gamma setup used by common
            # 240x320 modules.  Delays above/below reset and sleep-out are
            # required by the controller, otherwise it can stay blank.
            self._command(0xB2, 0x0C, 0x0C, 0x00, 0x33, 0x33)
            self._command(0xB7, 0x35)
            self._command(0xBB, 0x19)
            self._command(0xC0, 0x2C)
            self._command(0xC2, 0x01)
            self._command(0xC3, 0x12)
            self._command(0xC4, 0x20)
            self._command(0xC6, 0x0F)
            self._command(0xD0, 0xA4, 0xA1)
            self._command(
                0xE0,
                0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F,
                0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23,
            )
            self._command(
                0xE1,
                0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F,
                0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23,
            )
            self._command(self._INVON)
            self._command(self._NORON)
            self._command(self._DISPON)
            time.sleep(0.100)
            self.clear()

        def _command(self, command, *args):
            self._serial_interface.command(command)
            if args:
                self._send_data(args)

        def _send_data(self, data):
            """Send data in chunks accepted by spidev/luma."""
            if isinstance(data, int):
                data = (data,)
            for start in range(0, len(data), 4096):
                self._serial_interface.data(list(data[start:start + 4096]))

        def set_window(self):
            x0 = self._x_offset
            y0 = self._y_offset
            x1 = x0 + self._w - 1
            y1 = y0 + self._h - 1
            self._command(self._CASET, x0 >> 8, x0 & 0xFF,
                          x1 >> 8, x1 & 0xFF)
            self._command(self._RASET, y0 >> 8, y0 & 0xFF,
                          y1 >> 8, y1 & 0xFF)
            self._command(self._RAMWR)

        def display(self, image):
            if image.mode != self.mode or image.size != self.size:
                raise ValueError(
                    f"expected RGB image {self.size}, got {image.mode} {image.size}"
                )
            image = self.preprocess(image)
            self.set_window()
            self._send_data(_rgb565_bytes(image))

        def cleanup(self):
            # Do not clear the panel during normal close: the final frame is
            # useful while diagnosing the wiring, and the caller controls BLK.
            try:
                self._serial_interface.cleanup()
            except Exception:
                pass
else:
    _ST7789Device = None


class Display:
    def __init__(self):
        self.dev = None
        self._gpio = None
        self._font_cache = {}

        if _ST7789Device is None:
            print("[lcd] luma.core/Pillow unavailable, fallback to console")
            return

        try:
            serial = spi(
                port=config.LCD_SPI_PORT,
                device=config.LCD_SPI_DEVICE,
                gpio_DC=config.LCD_DC_PIN,
                gpio_RST=config.LCD_RESET_PIN,
                bus_speed_hz=config.LCD_SPI_SPEED_HZ,
                reset_hold_time=0.05,
                reset_release_time=0.15,
            )
            self.dev = _ST7789Device(
                serial,
                width=config.LCD_WIDTH,
                height=config.LCD_HEIGHT,
                rotate=config.LCD_ROTATE,
                x_offset=getattr(config, "LCD_X_OFFSET", 0),
                y_offset=getattr(config, "LCD_Y_OFFSET", 0),
                bgr=getattr(config, "LCD_BGR", False),
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
        if self.dev is not None:
            try:
                self.dev.cleanup()
            except Exception as exc:
                print(f"[lcd] cleanup failed: {exc}")
        self.dev = None


__all__ = ["Display"]
