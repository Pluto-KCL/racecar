"""停车标志模块，兼容二维码 P 和蓝色方形标志。"""
import cv2
from config import CFG

class ParkingDetector:
    def __init__(self):
        self.qr = cv2.QRCodeDetector()
    def detect(self, frame):
        text, _, _ = self.qr.detectAndDecode(frame)
        if text and text.lower() in ('p', 'parking', '车库', '停车'):
            return True
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, (90, 70, 50), (140, 255, 255))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return any(cv2.contourArea(c) >= CFG.parking_sign_min_area for c in contours)
