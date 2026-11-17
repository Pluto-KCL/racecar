#!/usr/bin/env python3
"""批量回放：跑一个样本文件夹，算识别准确率。这是 11-21"指示牌 ≥80%"的验收工具。

用法：
    python3 tools/replay.py media/capture/left   --kind sign
    python3 tools/replay.py media/capture/right  --kind sign
    python3 tools/replay.py media/capture/color  --kind color

标签从文件名前缀取（left_001.jpg → left）。
"""

import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2  # noqa: E402

import protocol as proto  # noqa: E402
from color_order import detect_color_order  # noqa: E402
from sign import detect_sign  # noqa: E402

NAME2SIGN = {"none": 0, "left": 1, "right": 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--kind", choices=["sign", "color"], default="sign")
    ap.add_argument("--min-quality", type=int, default=40)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.folder, "*.jpg")))
    if not files:
        print(f"没有图片：{args.folder}")
        return

    ok = 0
    detail = []
    for f in files:
        img = cv2.imread(f)
        label = os.path.basename(f).split("_")[0]
        if args.kind == "sign":
            r = detect_sign(img)
            expect = NAME2SIGN.get(label, 0)
            got = r["sign"] if r["quality"] >= args.min_quality else 0
            hit = got == expect
            detail.append((os.path.basename(f), expect, got, r["quality"], hit))
        else:
            r = detect_color_order(img)
            hit = bool(r["valid"])
            detail.append((os.path.basename(f), "4色", len(r["colors"]), r["quality"], hit))
        ok += hit

    n = len(files)
    print(f"\n{'file':22s} {'expect':>7s} {'got':>5s} {'q':>4s}  ok")
    for d in detail:
        print(f"{d[0]:22s} {str(d[1]):>7s} {str(d[2]):>5s} {d[3]:>4d}  {'✓' if d[4] else '✗'}")
    print(f"\n准确率 {ok}/{n} = {100.0 * ok / n:.1f}%   (验收线：指示牌 ≥ 80%)")


if __name__ == "__main__":
    main()
