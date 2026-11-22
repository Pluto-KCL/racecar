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
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vision", "project"))

from protocol import pack_frame, encode_seq   # noqa: E402

ORDERS = [
    ["red", "green", "blue", "yellow"],
    ["red", "green", "yellow", "blue"],
    ["yellow", "blue", "red", "green"],
    ["green", "yellow", "red", "blue"],
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

    command = {"sign": 0, "seq": None, "quality": 90}
    command_lock = threading.Lock()
    stop_heartbeat = threading.Event()

    def heartbeat():
        while not stop_heartbeat.is_set():
            with command_lock:
                current = dict(command)
            send(ser, current["sign"], current["seq"], current["quality"])
            stop_heartbeat.wait(0.04)

    heartbeat_thread = threading.Thread(target=heartbeat, name="vision-heartbeat", daemon=True)
    heartbeat_thread.start()

    i = 0
    while True:
        try:
            cmd = input("cmd> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd in ("q", "quit", "exit"):
            break
        elif cmd in ("1", "l"):
            with command_lock:
                command.update(sign=1, seq=None)
            print("已设置：左转")
        elif cmd in ("2", "r"):
            with command_lock:
                command.update(sign=2, seq=None)
            print("已设置：右转")
        elif cmd in ("0", "n"):
            with command_lock:
                command.update(sign=0, seq=None)
            print("已发：无指示")
        elif cmd == "c":
            seq = ORDERS[i % len(ORDERS)]
            i += 1
            with command_lock:
                command.update(sign=0, seq=seq)
            print(f"已发颜色：{seq}")
        elif cmd == "a":
            print("自动模式，Ctrl+C 停")
            try:
                while True:
                    s = random.choice([0, 0, 1, 2])
                    seq = random.choice(ORDERS) if random.random() < 0.5 else None
                    with command_lock:
                        command.update(sign=s, seq=seq)
                    print(f"  auto sign={s} seq={seq}")
                    time.sleep(2.0)
            except KeyboardInterrupt:
                print("停")
        else:
            print("看不懂，输 1/2/0/c/a/q")

    stop_heartbeat.set()
    heartbeat_thread.join(timeout=1.0)
    ser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
