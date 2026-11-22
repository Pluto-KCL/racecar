#!/usr/bin/env python3
"""
view_frames.py — PC 侧串口监视器

用途：
  1) 树莓派还没到货时，先用笔记本 + USB-TTL 验证 STM32 的接收和校验
  2) 实车时把树莓派拔下来夹在 STM32 上，看帧有没有真的进来

用法：
  python tools/view_frames.py COM3
  python tools/view_frames.py /dev/ttyUSB0 --baud 115200
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vision", "project"))

from protocol import parse_frame, decode_seq   # noqa: E402

NAMES = {0: "红", 1: "绿", 2: "蓝", 3: "黄"}
SIGN = {0: "无", 1: "左", 2: "右", 3: "车库"}


def consume_frames(buf):
    """从缓冲区消费完整帧，遇到噪声时只前移到下一个帧头。"""
    frames = []
    bad = 0
    header = b"\xAA\x55"
    while True:
        start = buf.find(header)
        if start < 0:
            if buf and buf[-1] == header[0]:
                del buf[:-1]
            else:
                buf.clear()
            break
        if start:
            del buf[:start]
        if len(buf) < 7:
            break
        raw = bytes(buf[:7])
        del buf[:7]
        parsed = parse_frame(raw)
        if (parsed is None or not parsed["checksum_ok"] or
                parsed["sign"] > 3 or parsed["color_valid"] > 1 or
                parsed["quality"] > 100):
            bad += 1
        else:
            frames.append(parsed)
    return frames, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("port", help="COM3 或 /dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=115200)
    args = ap.parse_args()

    try:
        import serial
    except ImportError:
        print("缺 pyserial：pip install pyserial")
        return 1

    ser = serial.Serial(args.port, args.baud, timeout=0.05)
    print(f"打开 {args.port} @ {args.baud}，Ctrl+C 退出")

    buf = bytearray()
    n_ok = n_bad = 0
    t0 = time.time()

    try:
        while True:
            buf += ser.read(64)
            frames, bad = consume_frames(buf)
            n_bad += bad
            for f in frames:
                n_ok += 1
                seq = [NAMES[c] for c in decode_seq(f["color_seq"])]
                print(f"[{n_ok:5d}] sign={SIGN.get(f['sign'], '非法'):2s} "
                      f"q={f['quality']:3d} color={'无' if not f['color_valid'] else '-'.join(seq)}")
            if (time.time() - t0) > 5:
                t0 = time.time()
                print(f"--- 5s: 好帧 {n_ok} / 坏帧 {n_bad} ---")
    except KeyboardInterrupt:
        print(f"\n退出：好帧 {n_ok}，坏帧 {n_bad}")
    finally:
        ser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
