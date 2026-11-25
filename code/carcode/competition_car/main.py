"""比赛单机程序：循迹、避障、识别、转向和倒车入库。"""

import argparse
import time
from collections import deque
from config import CFG
from car import Car
from vision import Vision


def stable(values, count):
    if len(values) < count:
        return None
    value = values[-1]
    return value if all(item == value for item in list(values)[-count:]) else None


def run(mode):
    car, vision = Car(), Vision()
    signs, colors = deque(maxlen=CFG.sign_confirm_frames), deque(maxlen=CFG.color_confirm_frames)
    last_sign = 0
    try:
        while True:
            frame = vision.read()
            if frame is None:
                car.stop()
                time.sleep(0.1)
                continue
            if mode in ("competition", "line"):
                result = vision.line_error(frame)
                distance = car.distance_cm()
                if distance is not None and distance < CFG.obstacle_stop_cm:
                    car.stop()
                    time.sleep(0.05)
                    continue
                if result is None:
                    car.stop()
                    continue
                error, derivative = result
                correction = CFG.line_kp * error * 100 + CFG.line_kd * derivative * 100
                correction = max(-CFG.line_max_correction, min(CFG.line_max_correction, correction))
                # 麦克纳姆轮用左右差速近似循迹，实车方向反转只修改 motor_invert。
                car.set_motors(CFG.line_speed - correction, CFG.line_speed - correction,
                               CFG.line_speed + correction, CFG.line_speed + correction)
                if mode == "competition":
                    detected = vision.sign(frame)
                    signs.append(detected)
                    confirmed = stable(signs, CFG.sign_confirm_frames)
                    if confirmed in (1, 2) and confirmed != last_sign:
                        car.stop()
                        car.rotate(28 if confirmed == 1 else -28)
                        time.sleep(CFG.sign_turn_seconds)
                        last_sign = confirmed
                    detected_colors = vision.colors(frame)
                    if detected_colors is not None:
                        colors.append(tuple(detected_colors))
                        confirmed_colors = stable(colors, CFG.color_confirm_frames)
                        if confirmed_colors is not None:
                            print("color sequence:", confirmed_colors, flush=True)
            elif mode == "obstacle":
                distance = car.distance_cm()
                if distance is not None and distance < CFG.obstacle_stop_cm:
                    car.stop(); time.sleep(0.2); car.strafe(25); time.sleep(0.5)
                else:
                    car.forward(28)
            elif mode == "parking":
                car.forward(25); time.sleep(0.5)
                car.stop(); car.rotate(25); time.sleep(CFG.parking_turn_seconds)
                car.set_motors(-22, -22, -22, -22); time.sleep(CFG.parking_reverse_seconds)
                car.stop(); time.sleep(CFG.parking_stop_seconds)
                return
    finally:
        car.close(); vision.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("competition", "line", "obstacle", "parking"), default="competition")
    run(parser.parse_args().mode)
