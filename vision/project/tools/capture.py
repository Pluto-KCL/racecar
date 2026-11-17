#!/usr/bin/env python3
"""采集样本：把摄像头画面存成带标签的图片，供离线调阈值。

用法（在 vision/ 目录下）：
    python3 tools/capture.py --label left  --n 30
    python3 tools/capture.py --label right --n 30
    python3 tools/capture.py --label none  --n 30
    python3 tools/capture.py --label color --n 40 --interval 1.0

拍的时候请按真实比赛条件：同样的距离、同样的光照、牌放同样的高度。
在宿舍白墙上拍出来的样本，到赛场一定不 work。
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2  # noqa: E402

from camera import Camera  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="left / right / none / color")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--interval", type=float, default=0.5, help="每张间隔秒数")
    ap.add_argument("--out", default="media/capture")
    args = ap.parse_args()

    outdir = os.path.join(args.out, args.label)
    os.makedirs(outdir, exist_ok=True)

    cam = Camera()
    print(f"[capture] saving {args.n} frames to {outdir}")
    saved = 0
    try:
        while saved < args.n:
            frame = cam.read()
            if frame is None:
                continue
            path = os.path.join(outdir, f"{args.label}_{saved:03d}.jpg")
            cv2.imwrite(path, frame)
            saved += 1
            print(f"  {saved}/{args.n}  {path}")
            time.sleep(args.interval)
    finally:
        cam.release()
    print("[capture] done")


if __name__ == "__main__":
    main()
