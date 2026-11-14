"""跨帧状态：指示牌短暂保持后失效；颜色连续确认后锁存。

不依赖摄像头或 OpenCV，可在 PC 上独立测试。
"""

import config
import protocol as proto


class RecognitionState:
    def __init__(self):
        self.sign = proto.SIGN_NONE
        self.sign_quality = 0
        self.colors = []
        self.color_quality = 0
        self._candidate = proto.SIGN_NONE
        self._sign_count = 0
        self._misses = 0
        self._color_candidate = ()
        self._color_count = 0

    def update_sign(self, sign, quality):
        if sign not in (proto.SIGN_LEFT, proto.SIGN_RIGHT) or quality < config.SIGN_MIN_QUALITY:
            self._candidate = proto.SIGN_NONE
            self._sign_count = 0
            self._misses += 1
            if self._misses >= config.SIGN_LOST_FRAMES:
                self.sign, self.sign_quality = proto.SIGN_NONE, 0
            return
        self._misses = 0
        if sign != self._candidate:
            self._candidate, self._sign_count = sign, 0
            # 出现反向候选时停止发送旧方向，等待新方向确认。
            self.sign, self.sign_quality = proto.SIGN_NONE, 0
        self._sign_count += 1
        if self._sign_count >= config.SIGN_CONFIRM_FRAMES:
            self.sign, self.sign_quality = sign, quality

    def update_colors(self, colors, valid, quality):
        if self.colors:
            return  # 直到本次运行结束，OLED 持续保留已确认顺序
        candidate = tuple(colors)
        if (not valid or quality < config.COLOR_MIN_QUALITY or
                len(candidate) != 4 or set(candidate) != set(proto.COLOR_CODE)):
            self._color_candidate, self._color_count = (), 0
            return
        if candidate != self._color_candidate:
            self._color_candidate, self._color_count = candidate, 0
        self._color_count += 1
        if self._color_count >= config.COLOR_CONFIRM_FRAMES:
            self.colors, self.color_quality = list(candidate), quality

    def pack(self):
        # 协议只有一个 quality。存在转向时必须反映转向置信度，
        # 不能让历史颜色的高置信度抬高当前指示牌置信度。
        quality = self.sign_quality if self.sign else self.color_quality
        return proto.pack_frame(self.sign, bool(self.colors),
                                proto.encode_seq(self.colors) if self.colors else 0,
                                quality)
