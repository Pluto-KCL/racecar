#!/usr/bin/env python3
"""五档曝光横扫：一次开相机跑完 4000~12000 us，存图并打印可比较的数字。

为什么不用手改 config.py 五次：
  * 每改一次要重启程序，中途光照一变，五档就不可比了；
  * 人眼对"稍微亮一点"不敏感，但对 sign.py 的白掩膜影响很大。

用法（在 vision/project 下）：
    source ../../.venv/bin/activate
    python tools/sweep_exposure.py --tag static --n 10
    python tools/sweep_exposure.py --tag moving --n 10 --interval 0.2
    python tools/sweep_exposure.py --tag static --levels 6000 8000 10000

输出：
    media/exposure/<tag>/<us>/<us>_000.jpg ...
    控制台一张汇总表（每档取中位数）：
      us    亮度V   蓝区S中位   蓝像素   白像素   过曝%    白过曝%

拍照要求：同一位置、同一光照、同一块牌。moving 组请一边轻推小车一边拍。
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

import config
from camera import Camera

DEFAULT_LEVELS = [4000, 6000, 8000, 10000, 12000]


def measure(bgr):
    """返回一帧的客观指标，用于跨曝光档比较。"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h_ch, s_ch, v_ch = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

    # 蓝底掩膜：和 sign.py 用同一组阈值，这样指标和实际识别口径一致
    lo, hi = config.SIGN_BLUE_HSV
    blue = cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
    blue_px = int(cv2.countNonZero(blue))
    # 只统计牌面内部的饱和度；整幅图会被灰地面和墙面拉偏
    blue_sat = float(np.median(s_ch[blue > 0])) if blue_px > 200 else float("nan")

    # 白色箭头候选：低饱和 + 高亮度
    white = cv2.inRange(
        hsv,
        np.array((0, 0, config.SIGN_WHITE_MIN_V), np.uint8),
        np.array((179, config.SIGN_WHITE_MAX_S, 255), np.uint8),
    )
    white_px = int(cv2.countNonZero(white))

    total = v_ch.size
    clip = float(np.count_nonzero(v_ch >= 250) / total)
    white_clip = (
        float(np.count_nonzero(v_ch[white > 0] >= 250) / white_px)
        if white_px else 0.0
    )

    return {
        "mean_v": float(v_ch.mean()),
        "blue_px": blue_px,
        "blue_sat": blue_sat,
        "white_px": white_px,
        "clip": clip,
        "white_clip": white_clip,
    }


def _med(values):
    arr = np.array([v for v in values if not np.isnan(v)], dtype=float)
    return float(np.median(arr)) if arr.size else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="static", help="存图子目录名，如 static / moving")
    ap.add_argument("--levels", type=int, nargs="+", default=DEFAULT_LEVELS)
    ap.add_argument("--n", type=int, default=10, help="每档拍几张")
    ap.add_argument("--interval", type=float, default=0.5)
    ap.add_argument("--out", default="media/exposure")
    ap.add_argument("--no-lock-awb", dest="lock_awb", action="store_false",
                    help="默认锁 AWB，五档才可比；PC 回退时本参数无效")
    args = ap.parse_args()

    cam = Camera()
    picam = getattr(cam, "_picam", None)
    if picam is None:
        print("[sweep] 当前是 PC 回退模式，曝光不可控，本脚本只在树莓派上有意义")
    elif args.lock_awb:
        try:
            for _ in range(5):
                cam.read()                       # 让 AWB 先收敛
            gains = picam.capture_metadata().get("ColourGains", (1.0, 1.0))
            picam.set_controls({"AwbEnable": False, "ColourGains": gains})
            print(f"[sweep] AWB 已锁定 gains={gains}，五档可公平比较")
        except Exception as exc:
            print(f"[sweep] AWB 锁定失败（不影响取图，继续）: {exc}")

    results = []
    try:
        for us in args.levels:
            cam.set_exposure(us)
            time.sleep(0.8)
            for _ in range(5):                   # 丢掉切换瞬间的几帧
                cam.read()

            outdir = os.path.join(args.out, args.tag, str(us))
            os.makedirs(outdir, exist_ok=True)

            stats = []
            saved = 0
            while saved < args.n:
                frame = cam.read()
                if frame is None:
                    time.sleep(0.05)
                    continue
                cv2.imwrite(os.path.join(outdir, f"{us}_{saved:03d}.jpg"), frame)
                stats.append(measure(frame))
                saved += 1
                print(f"  [{us} us] {saved}/{args.n}")
                time.sleep(args.interval)
            results.append((us, stats))
    finally:
        cam.release()

    print("\n" + "=" * 72)
    print(f"{'us':>6} {'亮度V':>8} {'蓝区S中位':>10} {'蓝像素':>8} "
          f"{'白像素':>8} {'过曝%':>7} {'白过曝%':>8}")
    print("-" * 72)
    for us, stats in results:
        print(f"{us:>6} "
              f"{_med([s['mean_v'] for s in stats]):>8.1f} "
              f"{_med([s['blue_sat'] for s in stats]):>10.1f} "
              f"{int(_med([s['blue_px'] for s in stats])):>8} "
              f"{int(_med([s['white_px'] for s in stats])):>8} "
              f"{100 * _med([s['clip'] for s in stats]):>7.2f} "
              f"{100 * _med([s['white_clip'] for s in stats]):>8.2f}")
    print("=" * 72)
    print("选档规则：")
    print("  1) 蓝区S中位 >= 90（远高于 SIGN_BLUE_HSV 的 S 下限 65）")
    print("  2) 白过曝% <= 5（白箭头不能一片 255，否则质心算不准）")
    print("  3) 白像素 >= 40（远处牌至少还能凑出箭头形状）")
    print("  4) 三条都对不上时优先保 (2)(3)，蓝区S 可用 HSV 放宽补回来")
    print("选中的值写回 config.py 的 EXPOSURE_US，然后才调 HSV。")


if __name__ == "__main__":
    main()
