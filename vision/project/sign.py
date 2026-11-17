"""交通指示牌识别（左转 / 右转 / 无）。

给 C 的输出：sign = 0/1/2 与 quality = 0..100。
不决定怎么转、转多少 —— 那是 STM32 的事。

当前实现是"能跑通的笨办法"，适合 20 天：
  1) 只在 SIGN_ROI（画面上半部分）里找
  2) 用颜色/亮度把牌面从背景里分出来（牌面明显比地面/背景亮或颜色饱和）
  3) 取最大轮廓，算它的中心 x
  4) 中心偏左 → 认为牌在左侧 → LEFT；偏右 → RIGHT
  5) quality 用"轮廓面积 / 期望面积"和"形状是否像菱形"综合

⚠️ 这一步必须用真实牌子的照片校准（tools/capture.py 拍 50 张，tools/tune_sign.py 调阈值）。
   在宿舍空想阈值 = 白干。
"""

import cv2
import numpy as np

import config
import protocol as proto

_state = {"last": proto.SIGN_NONE, "count": 0}


def _mask_sign(roi_bgr):
    """把"像指示牌"的像素挑出来。TODO: 按实测照片改这里。"""
    hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
    # 落选方案参考：
    #   a) 高饱和（彩色牌）：S > 80
    #   b) 高亮度（白底黑字牌）：V > 180
    #   c) 特定颜色：按牌子的实际颜色定 HSV 区间
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]
    mask = ((s > 80) & (v > 60)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return mask


def detect_sign(frame_bgr):
    """返回 {'sign': 0/1/2, 'quality': 0-100, 'cx': 归一化中心x 或 None}"""
    if frame_bgr is None or frame_bgr.size == 0:
        return {"sign": proto.SIGN_NONE, "quality": 0, "cx": None}
    x1, y1, x2, y2 = config.SIGN_ROI
    roi = frame_bgr[y1:y2, x1:x2]
    if roi.size == 0:
        return {"sign": proto.SIGN_NONE, "quality": 0, "cx": None}

    mask = _mask_sign(roi)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {"sign": proto.SIGN_NONE, "quality": 0, "cx": None}

    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    if area < config.SIGN_MIN_AREA:
        return {"sign": proto.SIGN_NONE, "quality": 0, "cx": None}

    m = cv2.moments(c)
    cx = m["m10"] / m["m00"] if m["m00"] else roi.shape[1] / 2
    cx_norm = cx / roi.shape[1]          # 0=最左, 1=最右

    # 置信度：面积占比 + 离画面中心的偏离程度
    area_score = min(1.0, area / (config.SIGN_MIN_AREA * 4))
    center_bias = abs(cx_norm - 0.5) * 2          # 0=正中, 1=最边
    quality = int(100 * (0.6 * area_score + 0.4 * center_bias))

    if cx_norm < 0.45:
        sign = proto.SIGN_LEFT
    elif cx_norm > 0.55:
        sign = proto.SIGN_RIGHT
    else:
        sign = proto.SIGN_NONE       # 正中 = 还没走到岔口，先不动

    return {"sign": sign, "quality": quality, "cx": float(cx_norm)}


def confirm(sign: int, quality: int):
    """多帧确认：连续 SIGN_CONFIRM_FRAMES 帧同向才输出，否则输出 NONE。

    STM32 那边也有一层保护（见 docs/03 §4），这里的目的是让 quality 有意义：
    单帧抖动不该让车突然转向。
    """
    if quality < config.SIGN_MIN_QUALITY or sign == proto.SIGN_NONE:
        _state["count"] = 0
        return proto.SIGN_NONE

    if sign == _state["last"]:
        _state["count"] += 1
    else:
        _state["last"] = sign
        _state["count"] = 1

    if _state["count"] >= config.SIGN_CONFIRM_FRAMES:
        return sign
    return proto.SIGN_NONE


__all__ = ["detect_sign", "confirm"]
