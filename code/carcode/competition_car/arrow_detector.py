"""交通箭头检测模块。返回 left、right 或 None，并使用轮廓三角形方向判断。"""
import cv2
import numpy as np
from config import CFG

class ArrowDetector:
    def detect(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, (0, 60, 50), (179, 255, 255))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in sorted(contours, key=cv2.contourArea, reverse=True):
            if cv2.contourArea(c) < CFG.arrow_min_area:
                continue
            x, y, w, h = cv2.boundingRect(c)
            if h == 0 or not 0.35 < w / h < 2.8:
                continue
            m = cv2.moments(c)
            if m['m00'] == 0:
                continue
            cx = m['m10'] / m['m00']
            return 'left' if cx < frame.shape[1] / 2 else 'right'
        return None
