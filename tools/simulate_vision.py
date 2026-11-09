#!/usr/bin/env python3
"""
simulate_vision.py — 假装自己是树莓派

为什么需要它：
  第 2 天你就能测掉「串口协议 + 状态机」这半条链路，不用等树莓派到货。
  指令是键盘输入的，所以 SSH、串口终端里都能用。

用法：
  python tools/simulate_vision.py COM3

交互：
  1 / l  → 发左转帧（连发 5 帧，模拟多帧确认）
  2 / r  → 发右转帧
  0 / n  → 发无指示帧
  c      → 轮流发 红绿蓝黄 / 随机顺序
  a      → 自动模式：每 2 秒随机发一种，Ctrl+C 停
  q      → 退出
"""
import argparse
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vision"))

from protocol import pack_frame, encode_seq   # noqa: E402

ORDERS = [
    [0, 1, 2, 3],   # 红绿蓝黄
    [0, 1, 3, 2],
    [3, 2, 0, 1],
    [1, 3, 0, 2],
]


def send(ser, sign, seq=None, quality=90):
    if seq is None:
        seq_i, valid = 0, 0
    else:
        seq_i, valid = encode_seq(seq), 1
    ser.write(pack_frame(sign, valid, seq_i, quality))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("port")
    ap.add_argument("--baud", type=int, default=115200)
    args = ap.parse_args()

    try:
        import serial
    except ImportError:
        print("缺 pyserial：pip install pyserial")
        return 1

    ser = serial.Serial(args.port, args.baud, timeout=0.1)
    print(__doc__)

    i = 0
    while True:
        try:
            cmd = input("cmd> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd in ("q", "quit", "exit"):
            break
        elif cmd in ("1", "l"):
            for _ in range(5):
                send(ser, 1)
                time.sleep(0.04)
            print("已发：左转 x5")
        elif cmd in ("2", "r"):
            for _ in range(5):
                send(ser, 2)
                time.sleep(0.04)
            print("已发：右转 x5")
        elif cmd in ("0", "n"):
            send(ser, 0)
            print("已发：无指示")
        elif cmd == "c":
            seq = ORDERS[i % len(ORDERS)]
            i += 1
            send(ser, 0, seq)
            print(f"已发颜色：{seq}")
        elif cmd == "a":
            print("自动模式，Ctrl+C 停")
            try:
                while True:
                    s = random.choice([0, 0, 1, 2])
                    seq = random.choice(ORDERS) if random.random() < 0.5 else None
                    send(ser, s, seq)
                    print(f"  auto sign={s} seq={seq}")
                    time.sleep(2.0)
            except KeyboardInterrupt:
                print("停")
        else:
            print("看不懂，输 1/2/0/c/a/q")

    ser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
