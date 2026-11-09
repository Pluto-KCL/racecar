#!/usr/bin/env python3
"""调参可视化：把"程序以为的牌"画出来，和原图并排存盘。

用法：
    python3 tools/tune_sign.py media/capture/left
    python3 tools/tune_sign.py media/capture/left/left_001.jpg --show

为什么不用滑块界面：树莓派多半是 SSH 连着跑，没有桌面。
存成图片让你 scp 回电脑看，比在现场开窗口靠谱。
看什么：mask 里应该是"一整块牌"，如果碎成渣或者把背景也框进来，就调 config.SIGN_* 或 _mask_sign()。
"""

import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

import config  # noqa: E402
import sign as sign_mod  # noqa: E402


def process(path, outdir):
    img = cv2.imread(path)
    if img is None:
        print(f"读不了：{path}")
        return
    x1, y1, x2, y2 = config.SIGN_ROI
    roi = img[y1:y2, x1:x2].copy()

    mask = sign_mod._mask_sign(roi)
    r = sign_mod.detect_sign(img)

    vis = roi.copy()
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        cv2.drawContours(vis, [c], -1, (0, 255, 0), 2)
    name = {0: "NONE", 1: "LEFT", 2: "RIGHT"}[r["sign"]]
    cv2.putText(vis, f"{name} q={r['quality']} cx={r['cx']}", (8, 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    mask3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    combo = np.hstack([roi, mask3, vis])

    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "dbg_" + os.path.basename(path))
    cv2.imwrite(out, combo)
    print(f"{os.path.basename(path):24s} -> {name:5s} q={r['quality']:3d}  {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="图片或文件夹")
    ap.add_argument("--out", default="media/tune")
    ap.add_argument("--show", action="store_true", help="有桌面时直接弹窗（按任意键继续）")
    args = ap.parse_args()

    files = [args.path] if os.path.isfile(args.path) else sorted(glob.glob(os.path.join(args.path, "*.jpg")))
    if not files:
        print("没有图片")
        return

    if args.show:
        for f in files:
            img = cv2.imread(f)
            process(f, args.out)
            if img is not None:
                cv2.imshow("orig", img)
                cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        for f in files:
            process(f, args.out)


if __name__ == "__main__":
    main()
