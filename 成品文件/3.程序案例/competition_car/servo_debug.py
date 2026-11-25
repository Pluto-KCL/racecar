"""二维云台调试程序。

用途是让操作者逐步调整水平 Pan 和俯仰 Tilt，找到摄像头正对车头的角度。
运行前把车轮抬离地面。输入角度后按回车，输入 c 保存当前角度为中心，输入 q 退出。
"""

import time

from car import Car
from config import CFG


def main():
    car = Car()
    if not car.ready:
        raise RuntimeError("未检测到 smbus/RPi.GPIO，只能在树莓派上调试舵机")
    pan, tilt = CFG.pan_center, CFG.tilt_center
    try:
        while True:
            car.set_servo_angle(CFG.pan_servo_channel, pan)
            car.set_servo_angle(CFG.tilt_servo_channel, tilt)
            print(f"当前角度 Pan={pan:.1f}°, Tilt={tilt:.1f}°")
            command = input("输入 pan/tilt，例如 90 50，或 c 保存中心，q 退出: ").strip().lower()
            if command == "q":
                break
            if command == "c":
                print("请把下面两行数值复制到 config.py 的 pan_center 和 tilt_center")
                print(f"pan_center = {pan:.1f}")
                print(f"tilt_center = {tilt:.1f}")
                continue
            values = command.replace(",", " ").split()
            if len(values) != 2:
                print("格式错误，需要输入两个角度")
                continue
            try:
                new_pan, new_tilt = map(float, values)
            except ValueError:
                print("角度必须是数字")
                continue
            if not (CFG.servo_min_angle <= new_pan <= CFG.servo_max_angle):
                print("Pan 超出 0~180 度范围")
                continue
            if not (CFG.servo_min_angle <= new_tilt <= CFG.servo_max_angle):
                print("Tilt 超出 0~180 度范围")
                continue
            pan, tilt = new_pan, new_tilt
            time.sleep(0.2)
    finally:
        car.stop()
        car.close()


if __name__ == "__main__":
    main()
