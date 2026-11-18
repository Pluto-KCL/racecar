"""实地图交通牌识别（左转、右转和车库 P 牌）。

赛场使用蓝底白色圆形箭头牌，车库入口旁另有蓝底白色 ``P`` 牌。旧实现把
“牌在画面左/右”当成转向方向，这在小车接近分叉口时会把同一块牌误判成相反
方向。本模块只把蓝色轮廓当候选，再用轮廓形状和内部白色图案判断牌型与方向。
"""

import cv2
import numpy as np

import config
import protocol as proto

_state = {"last": proto.SIGN_NONE, "count": 0}


def _blue_mask(roi_bgr):
    """返回实地图蓝底牌的二值掩膜。"""
    hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
    lo, hi = config.SIGN_BLUE_HSV
    mask = cv2.inRange(hsv, np.array(lo, dtype=np.uint8), np.array(hi, dtype=np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    return hsv, mask


def _mask_sign(roi_bgr):
    """调参工具兼容的接口：返回蓝底牌掩膜。"""
    return _blue_mask(roi_bgr)[1]


def _inner_and_white(hsv, contour, x, y, w, h):
    """提取轮廓内部的白色箭头/P，排除牌外的白墙。"""
    local_contour = contour.copy()
    local_contour[:, :, 0] -= x
    local_contour[:, :, 1] -= y
    inside = np.zeros((h, w), np.uint8)
    cv2.drawContours(inside, [local_contour], -1, 255, thickness=-1)
    # 侵蚀一圈，避免白色边框和轮廓抗锯齿进入图案统计。
    inside = cv2.erode(inside, np.ones((3, 3), np.uint8), iterations=1)
    patch = hsv[y:y + h, x:x + w]
    white = ((patch[:, :, 1] <= config.SIGN_WHITE_MAX_S) &
             (patch[:, :, 2] >= config.SIGN_WHITE_MIN_V)).astype(np.uint8) * 255
    white &= inside
    # 牌在 640x480 画面中可能只有几十像素，不能用开运算抹掉细箭头。
    white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
    return inside, white


def _white_ratio(white):
    return float(cv2.countNonZero(white)) / max(1, white.shape[0] * white.shape[1])


def _p_score(white):
    """粗略衡量白色图案是否像大写 P，而不是蓝色方块反光。"""
    n = cv2.countNonZero(white)
    if n == 0:
        return 0.0
    h, w = white.shape
    b = white > 0
    left = b[:, :max(1, int(w * 0.38))].sum() / n
    top = b[:max(1, int(h * 0.55)), int(w * 0.25):int(w * 0.9)].sum() / n
    mid_right = b[int(h * 0.18):int(h * 0.62), int(w * 0.42):].sum() / n
    bottom_left = b[int(h * 0.55):, :max(1, int(w * 0.45))].sum() / n
    return float(0.40 * left + 0.27 * top + 0.18 * mid_right + 0.15 * bottom_left)


def _arrow_direction(white):
    """根据箭头尖端偏向返回 (方向, 方向置信度)。"""
    n = cv2.countNonZero(white)
    if n == 0:
        return proto.SIGN_NONE, 0.0
    _ys, xs = np.nonzero(white)
    w = white.shape[1]
    # 90 度弯箭头的尖端会落在一侧的外缘，外缘比质心更抗透视变形。
    left_outer = float(np.count_nonzero(xs < w * 0.30)) / n
    right_outer = float(np.count_nonzero(xs > w * 0.70)) / n
    side_bias = right_outer - left_outer
    if abs(side_bias) < config.SIGN_ARROW_DEADZONE:
        center = float(xs.mean() / max(w, 1) - 0.5)
        side_bias = center * 1.8
    if abs(side_bias) < config.SIGN_ARROW_DEADZONE:
        return proto.SIGN_NONE, 0.0
    sign = proto.SIGN_RIGHT if side_bias > 0 else proto.SIGN_LEFT
    return sign, min(1.0, abs(side_bias) / 0.35)


def _shape_score(area, perimeter, w, h, approx_vertices):
    circularity = 4.0 * np.pi * area / max(perimeter * perimeter, 1.0)
    aspect = min(w, h) / max(w, h, 1)
    circle = min(1.0, max(0.0, (circularity - 0.45) / 0.45))
    square = min(1.0, max(0.0, (aspect - 0.55) / 0.35))
    # 近似四边形更像 P 牌，圆牌通常有更多顶点。
    square *= 1.0 if 4 <= approx_vertices <= 6 else 0.55
    return circularity, aspect, circle, square


def detect_sign(frame_bgr):
    """返回 ``sign``（0 无、1 左、2 右、3 车库）及 0..100 置信度。"""
    empty = {"sign": proto.SIGN_NONE, "quality": 0, "cx": None, "kind": "none"}
    if frame_bgr is None or frame_bgr.size == 0:
        return empty
    x1, y1, x2, y2 = config.SIGN_ROI
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(frame_bgr.shape[1], x2), min(frame_bgr.shape[0], y2)
    roi = frame_bgr[y1:y2, x1:x2]
    if roi.size == 0:
        return empty

    hsv, mask = _blue_mask(roi)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < config.SIGN_MIN_AREA:
            continue
        x, y, w, h = cv2.boundingRect(c)
        if w < 8 or h < 8:
            continue
        hull = cv2.convexHull(c)
        shape_area = cv2.contourArea(hull)
        shape_perimeter = cv2.arcLength(hull, True)
        approx = cv2.approxPolyDP(hull, 0.04 * shape_perimeter, True)
        circularity, aspect, circle_score, square_score = _shape_score(
            shape_area, shape_perimeter, w, h, len(approx)
        )
        _inside, white = _inner_and_white(hsv, c, x, y, w, h)
        white_ratio = _white_ratio(white)
        if (white_ratio < config.SIGN_MIN_WHITE_RATIO or
                cv2.countNonZero(white) < config.SIGN_MIN_WHITE_PIXELS):
            continue
        p_score = _p_score(white)
        arrow, arrow_score = _arrow_direction(white)
        area_score = min(1.0, area / (config.SIGN_MIN_AREA * 8.0))
        # 方形 P 牌的轮廓近似四边形；圆形箭头牌优先看圆度和箭头尖端。
        is_p = (square_score >= 0.45 and p_score >= 0.34 and
                circularity < max(0.86, config.SIGN_MIN_CIRCULARITY + 0.2))
        if is_p:
            quality = int(100 * (0.28 * area_score + 0.25 * square_score +
                                 0.25 * min(1.0, white_ratio / 0.12) + 0.22 * p_score))
            kind = "park"
            detected = proto.SIGN_PARK
        elif circularity >= config.SIGN_MIN_CIRCULARITY and arrow != proto.SIGN_NONE:
            quality = int(100 * (0.28 * area_score + 0.27 * circle_score +
                                 0.22 * min(1.0, white_ratio / 0.12) + 0.23 * arrow_score))
            kind = "arrow"
            detected = arrow
        else:
            continue
        m = cv2.moments(c)
        cx = (m["m10"] / m["m00"] if m["m00"] else x + w / 2.0)
        candidates.append({
            "sign": detected,
            "quality": max(0, min(100, quality)),
            "cx": float(cx / max(roi.shape[1], 1)),
            "kind": kind,
            "area": area,
        })

    if not candidates:
        return empty
    return max(candidates, key=lambda item: (item["quality"], item["area"]))


def confirm(sign: int, quality: int):
    """多帧确认，供离线工具使用；主循环由 RecognitionState 统一确认。"""
    if quality < config.SIGN_MIN_QUALITY or sign not in (
            proto.SIGN_LEFT, proto.SIGN_RIGHT, proto.SIGN_PARK):
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


__all__ = ["detect_sign", "confirm", "_mask_sign"]
