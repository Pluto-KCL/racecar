#!/usr/bin/env python3
"""树莓派主循环：取图 → 识别 → 打包 → 串口发送 → 屏幕显示。

运行：
    python3 main.py                 # 正常跑（发串口）
    python3 main.py --no-uart       # 不发串口，只在屏幕上/控制台看结果（先调算法用）
    python3 main.py --debug         # 存调试图到 media/debug/

设计原则：
  * 采集/识别/显示异常尽量降级；底层硬件调用仍可能阻塞。
  * 尽力按目标频率发送，识别频率可以更低。
  * 所有可调参数在 config.py。
"""

import argparse
import os
import threading
import time
from collections import deque

import cv2

import config
from camera import Camera
from color_order import detect_color_order
from lcd_display import Display
from sign import detect_sign
from recognition_state import RecognitionState
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
    last_t = time.monotonic()
    last_lcd = 0.0

    # 跨帧确认与失效策略独立于硬件调度。
    state = RecognitionState()
    frame_number = 0
    frame_lock = threading.Lock()
    stop_sender = threading.Event()
    latest_frame = state.pack()

    def send_loop():
        next_send = time.monotonic()
        while not stop_sender.is_set():
            with frame_lock:
                frame_out = latest_frame
            link.send(frame_out)
            next_send += period
            wait = max(0.0, next_send - time.monotonic())
            stop_sender.wait(wait)

    sender_thread = None
    if link is not None:
        sender_thread = threading.Thread(target=send_loop, name="uart-sender", daemon=True)
        sender_thread.start()
    if config.COLOR_MODE != "camera":
        cam.release()
        raise ValueError("主循环目前只支持 COLOR_MODE=camera；TCS34725 请单独校准使用")

    print(f"[main] start: {config.SEND_HZ} Hz, uart={'off' if args.no_uart else config.SERIAL_PORT}")

    try:
        while True:
            t0 = time.monotonic()
            try:
                frame = cam.read()
            except Exception as exc:
                print(f"[cam] read failed: {exc}")
                frame = None
            state.set_camera_ok(frame is not None)

            # ---- 指示牌（每帧都做，牌是"路过"的，漏了就没了）----
            try:
                s = detect_sign(frame) if frame is not None else {"sign": 0, "quality": 0}
            except Exception as exc:
                print(f"[sign] detection failed: {exc}")
                s = {"sign": 0, "quality": 0}
            state.update_sign(s["sign"], s["quality"])

            # ---- 颜色顺序（每 2 帧做一次，省 CPU）----
            if frame_number % config.COLOR_DETECT_EVERY == 0:
                try:
                    c = detect_color_order(frame) if frame is not None else {"colors": [], "valid": 0, "quality": 0}
                except Exception as exc:
                    print(f"[color] detection failed: {exc}")
                    c = {"colors": [], "valid": 0, "quality": 0}
                state.update_colors(c["colors"], c["valid"], c["quality"])
            frame_number += 1

            # ---- 发送 ----
            with frame_lock:
                latest_frame = state.pack()

            # ---- 显示（5 Hz 足够，避免 SPI 刷屏影响识别）----
            if t0 - last_lcd > 1.0 / config.LCD_REFRESH_HZ:
                last_lcd = t0
                try:
                    if state.colors:
                        disp.show_color_order(state.colors, state.color_quality)
                    else:
                        disp.show_status("RUN" if frame is not None else "NO CAMERA", state.sign, state.sign_quality)
                except Exception as exc:
                    print(f"[lcd] display failed: {exc}")

            if args.debug and frame is not None:
                try:
                    cv2.imwrite(os.path.join("media", "debug", f"f_{time.time_ns()}.jpg"), frame)
                except cv2.error as exc:
                    print(f"[debug] save failed: {exc}")

            # ---- 定频 ----
            fps_hist.append(1.0 / max(time.monotonic() - last_t, 1e-6))
            last_t = time.monotonic()
            dt = period - (time.monotonic() - t0)
            if dt > 0:
                time.sleep(dt)

    except KeyboardInterrupt:
        print("\n[main] stopped by user")
    finally:
        stop_sender.set()
        if sender_thread is not None:
            sender_thread.join(timeout=1.0)
        cam.release()
        if link is not None:
            link.close()
        disp.close()
        if fps_hist:
            print(f"[main] avg fps ~{sum(fps_hist) / len(fps_hist):.1f}")


if __name__ == "__main__":
    main()
