"""四色目标模块，编码为红0、绿1、蓝2、黄3。"""
from vision import Vision

class ColorDetector:
    def __init__(self, vision):
        self.vision = vision
    def detect(self, frame):
        return self.vision.colors(frame)
