"""摄像头、黑线、箭头和四颜色目标识别。"""

import cv2
import numpy as np
from collections import deque
from config import CFG
from camera import Camera


class Vision:
    def __init__(self):
        self.cap = Camera()
        self.last_error = 0.0
        self.error_history = deque(maxlen=5)

    def read(self):
        return self.cap.read()

    def line_error(self, frame):
        h, w = frame.shape[:2]
        y0, y1 = int(h * CFG.roi_top), int(h * CFG.roi_bottom)
        roi = frame[y0:y1]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        mask = cv2.inRange(gray, 0, CFG.line_gray_threshold)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        moments = cv2.moments(mask)
        if moments["m00"] < CFG.line_min_area:
            return None
        x = moments["m10"] / moments["m00"]
        error = (x - w / 2) / (w / 2)
        derivative = error - self.last_error
        self.last_error = error
        self.error_history.append(error)
        return error, derivative

    def sign(self, frame):
        """用红色/蓝色箭头牌的轮廓方向给出 left/right，需按现场牌面调阈值。"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        red = cv2.inRange(hsv, (0, 70, 60), (15, 255, 255)) | cv2.inRange(hsv, (160, 70, 60), (179, 255, 255))
        blue = cv2.inRange(hsv, (90, 70, 60), (135, 255, 255))
        mask = red | blue
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best = None
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 700:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            if best is None or area > best[0]:
                best = (area, x + w / 2, y + h / 2, w, h)
        if best is None:
            return 0
        _, cx, _, w, _ = best
        return 1 if cx < frame.shape[1] / 2 else 2

    def colors(self, frame):
        """按画面横向位置识别红绿蓝黄四个色块，返回编码列表或 None。"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        ranges = {
            0: [((0, 80, 60), (15, 255, 255)), ((160, 80, 60), (179, 255, 255))],
            1: [((35, 50, 40), (85, 255, 255))],
            2: [((90, 60, 40), (135, 255, 255))],
            3: [((18, 70, 60), (35, 255, 255))],
        }
        samples = []
        for code, limits in ranges.items():
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lo, hi in limits:
                mask |= cv2.inRange(hsv, lo, hi)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                if cv2.contourArea(contour) > 350:
                    x, _, w, _ = cv2.boundingRect(contour)
                    samples.append((x + w / 2, code))
        if len(samples) < 4:
            return None
        samples.sort()
        return [code for _, code in samples[:4]]

    def close(self):
        self.cap.release()
