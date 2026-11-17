"""摄像头封装：树莓派用 picamera2，PC 上用 cv2.VideoCapture 回退（B 在宿舍就能调）。

对外只暴露一个接口：Camera().read() -> BGR ndarray (h, w, 3) 或 None
"""

import config

try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None

import cv2
import numpy as np


class Camera:
    def __init__(self, width=None, height=None, exposure_us=None):
        self.width = width or config.CAM_WIDTH
        self.height = height or config.CAM_HEIGHT
        self.exposure_us = exposure_us or config.EXPOSURE_US
        self._picam = None
        self._cap = None
        self._open()

    def _open(self):
        if Picamera2 is not None:
            self._picam = Picamera2()
            cfg = self._picam.create_preview_configuration(
                main={"size": (self.width, self.height), "format": config.CAM_FORMAT}
            )
            self._picam.configure(cfg)
            self._picam.start()
            self.set_exposure(self.exposure_us)
            print("[cam] picamera2 started")
        else:
            # PC 调试：用笔记本摄像头。分辨率可能不是你设的值，属于正常。
            self._cap = cv2.VideoCapture(0)
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            print("[cam] fallback to cv2.VideoCapture(0) — 只在 PC 上调参时用")

    def set_exposure(self, us: int):
        """TUNABLE：现场调曝光。太小发黑、太大会拖影（车一动就糊）。"""
        self.exposure_us = int(us)
        if self._picam is not None:
            try:
                self._picam.set_controls({"ExposureTime": self.exposure_us, "AeEnable": False})
            except Exception as e:
                print(f"[cam] set_exposure failed: {e}")

    def read(self):
        if self._picam is not None:
            arr = self._picam.capture_array()          # RGB
            return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        if self._cap is not None:
            ok, frame = self._cap.read()
            return frame if ok else None
        return None

    def release(self):
        if self._picam is not None:
            self._picam.stop()
            self._picam.close()
        if self._cap is not None:
            self._cap.release()
