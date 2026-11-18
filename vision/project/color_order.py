"""按实地图四色目标的排列顺序识别颜色。

场地左侧颜色区沿赛道排成一列，手机照片中这列目标可能看起来是横排，也可能
是竖排；同时画面里还可能出现避障块或车库牌旁的额外黄色/蓝色物体。因此不能
简单取全图面积最大的四块再按 x 排序，而要先找出最接近一条直线的四个色块。
"""

from itertools import combinations

import cv2
import numpy as np

import config


def _color_of(hsv_px):
    """单个像素的 HSV -> 颜色名或 None。"""
    h, s, v = int(hsv_px[0]), int(hsv_px[1]), int(hsv_px[2])
    for name, ranges in config.COLOR_HSV.items():
        for lo, hi in ranges:
            if lo[0] <= h <= hi[0] and lo[1] <= s <= hi[1] and lo[2] <= v <= hi[2]:
                return name
    return None


def _axis_for(group, width, height):
    if config.COLOR_AXIS in ("x", "y"):
        return config.COLOR_AXIS
    xspan = (max(b["cx"] for b in group) - min(b["cx"] for b in group)) / max(width, 1)
    yspan = (max(b["cy"] for b in group) - min(b["cy"] for b in group)) / max(height, 1)
    return "x" if xspan >= yspan else "y"


def _fit_group(group, width, height):
    """返回 (axis, residual, span, area_spread, order)。"""
    axis = _axis_for(group, width, height)
    if axis == "x":
        t = np.array([b["cx"] / max(width, 1) for b in group], dtype=float)
        u = np.array([b["cy"] / max(height, 1) for b in group], dtype=float)
    else:
        t = np.array([b["cy"] / max(height, 1) for b in group], dtype=float)
        u = np.array([b["cx"] / max(width, 1) for b in group], dtype=float)
    order = np.argsort(t)
    span = float(t.max() - t.min())
    if span < 1e-6:
        residual = 1.0
    else:
        coeff = np.polyfit(t, u, 1)
        residual = float(np.median(np.abs(u - np.polyval(coeff, t))))
    areas = np.array([b["area"] for b in group], dtype=float)
    area_spread = float(areas.std() / max(areas.mean(), 1.0))
    return axis, residual, span, area_spread, order


def _choose_group(blobs, width, height):
    if len(blobs) == 4:
        return blobs
    # 现场通常只有 4~8 个彩色候选；限制组合数量，避免相机反光造成 CPU 峰值。
    pool = sorted(blobs, key=lambda b: b["area"], reverse=True)[:12]
    if len(pool) < 4:
        return []
    top_area = sum(b["area"] for b in pool[:4])
    best = None
    for group in combinations(pool, 4):
        axis, residual, span, area_spread, _order = _fit_group(group, width, height)
        if span < config.COLOR_MIN_AXIS_SPREAD:
            continue
        area_bonus = sum(b["area"] for b in group) / max(top_area, 1.0)
        # 共线优先，面积接近次之；面积总量只用于打破两组同样共线的平局。
        score = residual * 4.0 + area_spread * 0.45 - area_bonus * 0.12
        if best is None or score < best[0]:
            best = (score, group)
    return list(best[1]) if best else []


def detect_color_order(frame_bgr):
    """返回 ``{'colors': [...], 'valid': 0/1, 'quality': 0-100}``。"""
    if frame_bgr is None or frame_bgr.size == 0:
        return {"colors": [], "valid": 0, "quality": 0}
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    blobs = []

    for name, ranges in config.COLOR_HSV.items():
        mask = np.zeros(hsv.shape[:2], np.uint8)
        for lo, hi in ranges:
            mask |= cv2.inRange(hsv, np.array(lo), np.array(hi))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area < config.COLOR_MIN_AREA:
                continue
            x, y, w, h = cv2.boundingRect(c)
            blobs.append({"color": name, "area": area, "cx": x + w / 2.0,
                          "cy": y + h / 2.0, "x": x, "y": y, "w": w, "h": h})

    if len(blobs) < 4:
        return {"colors": [], "valid": 0, "quality": 0}

    selected = _choose_group(blobs, frame_bgr.shape[1], frame_bgr.shape[0])
    if len(selected) != 4:
        return {"colors": [], "valid": 0, "quality": 0}
    axis, residual, span, area_spread, order = _fit_group(
        selected, frame_bgr.shape[1], frame_bgr.shape[0]
    )
    selected = [selected[i] for i in order]
    if config.COLOR_ORDER_REVERSED:
        selected.reverse()

    colors = [b["color"] for b in selected]
    line_score = 1.0 - min(residual / max(config.COLOR_MAX_LINE_RESIDUAL, 1e-6), 1.0)
    area_score = 1.0 - min(area_spread, 1.0)
    quality = int(max(0, min(100, 100 * (0.55 * area_score + 0.45 * line_score))))
    valid = int(span >= config.COLOR_MIN_AXIS_SPREAD and
                residual <= config.COLOR_MAX_LINE_RESIDUAL and
                quality >= config.COLOR_MIN_QUALITY)
    return {"colors": colors if valid else [], "valid": valid,
            "quality": quality if valid else 0, "axis": axis,
            "residual": residual}


def draw_debug(frame_bgr, result):
    """调参用的可视化：把结果文字画到图上。"""
    out = frame_bgr.copy()
    text = "-".join(result.get("colors", [])) or "no-color"
    cv2.putText(out, f"{text} q={result.get('quality', 0)}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    return out


__all__ = ["detect_color_order", "draw_debug"]
