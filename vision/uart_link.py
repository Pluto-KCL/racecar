"""串口封装：打开、重连、发帧。断线不抛异常，只记日志并尝试重开。

用法：
    from uart_link import VisionLink
    link = VisionLink()
    link.send(pack_frame(...))     # 内部自动处理断线
"""

import time

import config

try:
    import serial
except ImportError:  # 没装 pyserial 时给出明确提示，而不是一堆 traceback
    serial = None


class VisionLink:
    def __init__(self, port=None, baud=None):
        self.port = port or config.SERIAL_PORT
        self.baud = baud or config.SERIAL_BAUD
        self._ser = None
        self._last_open_try = 0.0
        self.sent = 0
        self.failed = 0

    def _open(self):
        if serial is None:
            raise RuntimeError("没装 pyserial：python3 -m pip install pyserial")
        self._ser = serial.Serial(self.port, self.baud, timeout=0.05, write_timeout=0.05)
        time.sleep(0.2)
        self._ser.reset_output_buffer()

    def send(self, frame: bytes) -> bool:
        if self._ser is None:
            now = time.time()
            if now - self._last_open_try < 1.0:   # 重连不要每帧都试，会卡住主循环
                return False
            self._last_open_try = now
            try:
                self._open()
            except Exception as e:
                self.failed += 1
                print(f"[uart] open failed: {e}")
                return False
        try:
            self._ser.write(frame)
            self.sent += 1
            return True
        except Exception as e:
            print(f"[uart] write failed: {e}")
            self._ser = None
            self.failed += 1
            return False

    def close(self):
        if self._ser is not None:
            try:
                self._ser.close()
            finally:
                self._ser = None
