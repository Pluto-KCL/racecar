"""颜色顺序识别（摄像头方案，主方案）。

规则要求：颜色区在赛道外约 25 cm，4 个 10 cm 方块随机排列，
车载屏必须持续显示顺序（如 红-绿-蓝-黄），直到裁判记录。

本文件只负责"看图说话"：返回 ['red','green','blue','yellow'] 这样的列表。
怎么编码成 1 个字节、怎么发出去，是 protocol.py 的事。
什么时候停车看/看多久，是 STM32 的事（状态机 TIME_COLOR）。
"""

import cv2
import numpy as np

import config

# 按色块中心 x 排序后取前 4 个。NOTE: 第一次实车跑完要确认"行进方向 ↔ x 方向"是否一致，
# 若反了就把 ORDER_REVERSED 改成 True（一行的事，别改算法）。
ORDER_REVERSED = False


def _color_of(hsv_px):
    """单个像素的 HSV → 颜色名 或 None。用 config.COLOR_HSV 的区间。"""
    h, s, v = int(hsv_px[0]), int(hsv_px[1]), int(hsv_px[2])
    for name, ranges in config.COLOR_HSV.items():
        for lo, hi in ranges:
            if lo[0] <= h <= hi[0] and lo[1] <= s <= hi[1] and lo[2] <= v <= hi[2]:
                return name
    return None


def detect_color_order(frame_bgr):
    """返回 {'colors': [...], 'valid': 0/1, 'quality': 0-100}"""
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    blobs = []

    for name, ranges in config.COLOR_HSV.items():
        mask = np.zeros(hsv.shape[:2], np.uint8)
        for lo, hi in ranges:
            mask |= cv2.inRange(hsv, np.array(lo), np.array(hi))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area < config.COLOR_MIN_AREA:
                continue
            x, y, w, h = cv2.boundingRect(c)
            blobs.append({"color": name, "area": area, "cx": x + w / 2.0, "cy": y + h / 2.0})

    if len(blobs) < 4:
        return {"colors": [], "valid": 0, "quality": 0}

    # 取面积最大的 4 个（避免远处/反光的碎块），再按 x 排顺序
    blobs.sort(key=lambda b: b["area"], reverse=True)
    blobs = blobs[:4]
    blobs.sort(key=lambda b: b["cx"], reverse=ORDER_REVERSED)

    colors = [b["color"] for b in blobs]
    # 置信度：4 个块面积是否接近（差太多说明有遮挡或误识）
    areas = np.array([b["area"] for b in blobs], float)
    spread = areas.std() / max(areas.mean(), 1.0)
    quality = int(max(0, 100 * (1.0 - min(spread, 1.0))))
    valid = 1 if quality >= 30 else 0

    return {"colors": colors, "valid": valid, "quality": quality}


def draw_debug(frame_bgr, result):
    """调参用的可视化：把结果文字画到图上。正式跑时别调用（费 CPU）。"""
    out = frame_bgr.copy()
    text = "-".join(result.get("colors", [])) or "no-color"
    cv2.putText(out, f"{text} q={result.get('quality', 0)}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    return out


__all__ = ["detect_color_order", "draw_debug"]
