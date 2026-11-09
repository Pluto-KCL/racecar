#!/usr/bin/env python3
"""树莓派主循环：取图 → 识别 → 打包 → 串口发送 → 屏幕显示。

运行：
    python3 main.py                 # 正常跑（发串口）
    python3 main.py --no-uart       # 不发串口，只在屏幕上/控制台看结果（先调算法用）
    python3 main.py --debug         # 存调试图到 media/debug/

设计原则：
  * 主循环绝不阻塞。任何一步失败都只是"这一帧没有结果"，不能让程序挂掉。
  * 发送频率固定，识别频率可以更低（识别每 2 帧做一次也行）。
  * 所有可调参数在 config.py。
"""

import argparse
import os
import time
from collections import deque

import cv2

import config
import protocol as proto
from camera import Camera
from color_order import detect_color_order
from oled_display import Display
from sign import confirm, detect_sign
from uart_link import VisionLink


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--no-uart", action="store_true", help="不发串口")
    p.add_argument("--debug", action="store_true", help="保存调试图")
    p.add_argument("--port", default=None, help="覆盖串口设备")
    return p.parse_args()


def main():
    args = parse_args()
    cam = Camera()
    disp = Display()
    link = None if args.no_uart else VisionLink(port=args.port)

    if args.debug:
        os.makedirs(os.path.join("media", "debug"), exist_ok=True)

    period = 1.0 / config.SEND_HZ
    fps_hist = deque(maxlen=30)
    last_t = time.time()
    last_oled = 0.0

    # 当前的识别结果（识别比发送慢时，用上一次的结果继续发，不要发 0 打断）
    sign_out, sign_q = proto.SIGN_NONE, 0
    colors, color_valid, color_q = [], 0, 0

    print(f"[main] start: {config.SEND_HZ} Hz, uart={'off' if args.no_uart else config.SERIAL_PORT}")

    try:
        while True:
            t0 = time.time()
            frame = cam.read()
            if frame is None:
                time.sleep(0.01)
                continue

            # ---- 指示牌（每帧都做，牌是"路过"的，漏了就没了）----
            s = detect_sign(frame)
            stable = confirm(s["sign"], s["quality"])
            if stable != proto.SIGN_NONE:
                sign_out, sign_q = stable, s["quality"]
            elif s["sign"] == proto.SIGN_NONE:
                # 连续几帧没牌，才把 sign 清掉，避免抖
                if sign_q > 0:
                    sign_q = max(0, sign_q - 5)

            # ---- 颜色顺序（每 2 帧做一次，省 CPU）----
            if int(t0 * 1000) % 2 == 0 and config.COLOR_MODE == "camera":
                c = detect_color_order(frame)
                if c["valid"] and len(c["colors"]) == 4:
                    colors, color_valid, color_q = c["colors"], 1, c["quality"]

            # ---- 发送 ----
            seq = proto.encode_seq(colors) if color_valid else 0x00
            frame_out = proto.pack_frame(sign_out, color_valid, seq, max(sign_q, color_q))
            if link is not None:
                link.send(frame_out)

            # ---- 显示（5 Hz 就够，OLED 刷新慢）----
            if t0 - last_oled > 0.2:
                last_oled = t0
                if color_valid:
                    disp.show_color_order(colors, color_q)
                else:
                    disp.show_status("RUN", sign_out, sign_q)

            if args.debug:
                cv2.imwrite(os.path.join("media", "debug", f"f_{int(t0 * 1000)}.jpg"), frame)

            # ---- 定频 ----
            fps_hist.append(1.0 / max(time.time() - last_t, 1e-6))
            last_t = time.time()
            dt = period - (time.time() - t0)
            if dt > 0:
                time.sleep(dt)

    except KeyboardInterrupt:
        print("\n[main] stopped by user")
    finally:
        cam.release()
        if link is not None:
            link.close()
        if fps_hist:
            print(f"[main] avg fps ~{sum(fps_hist) / len(fps_hist):.1f}")


if __name__ == "__main__":
    main()
