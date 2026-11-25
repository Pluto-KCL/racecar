"""摄像头封装，优先使用 Picamera2，失败时回退到 OpenCV。输出 BGR。"""

import cv2
from config import CFG

try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None


class Camera:
    def __init__(self, width=None, height=None, exposure_us=None):
        self.width = width or CFG.camera_width
        self.height = height or CFG.camera_height
        self.exposure_us = exposure_us or CFG.exposure_us
        self._picam = None
        self._cap = None
        self._open()

    def _open(self):
        if Picamera2 is not None:
            self._picam = Picamera2()
            cfg = self._picam.create_preview_configuration(
                main={"size": (self.width, self.height), "format": CFG.camera_format}
            )
            self._picam.configure(cfg)
            self._picam.start()
            self.set_exposure(self.exposure_us)
            print("[cam] picamera2 started", flush=True)
            return
        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self._cap.release()
            self._cap = None
            raise RuntimeError("无法打开 /dev/video0")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        print("[cam] using cv2.VideoCapture(0)", flush=True)

    def set_exposure(self, exposure_us):
        self.exposure_us = int(exposure_us)
        if self._picam is not None:
            try:
                self._picam.set_controls({"ExposureTime": self.exposure_us, "AeEnable": False})
            except Exception as exc:
                print(f"[cam] exposure control unavailable: {exc}", flush=True)

    def read(self):
        if self._picam is not None:
            frame = self._picam.capture_array()
            if CFG.camera_format == "RGB888":
                return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        if self._cap is not None:
            ok, frame = self._cap.read()
            return frame if ok else None
        return None

    def release(self):
        if self._picam is not None:
            self._picam.stop()
            self._picam.close()
            self._picam = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None
