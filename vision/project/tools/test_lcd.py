#!/usr/bin/env python3
"""独立测试 ST7789 屏幕显示。

推荐在 ``vision`` 目录下运行：

    python tools/test_lcd.py

也可以从项目根目录运行：

    python vision/tools/test_lcd.py

脚本只使用 ``lcd_display.Display``，不会启动摄像头或串口。
"""

import argparse
import sys
import time
from pathlib import Path


# 将 vision 加入模块搜索路径，保证从项目根目录执行时也能导入 lcd_display。
VISION_DIR = Path(__file__).resolve().parents[1]
if str(VISION_DIR) not in sys.path:
    sys.path.insert(0, str(VISION_DIR))

from lcd_display import Display


def parse_args():
    parser = argparse.ArgumentParser(description="测试 ST7789 SPI 屏幕")
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="每个测试画面的停留秒数，默认 2 秒",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="完整测试循环次数，0 表示持续循环，默认 1 次",
    )
    return parser.parse_args()


def show_test_cycle(display, delay):
    """按顺序显示几组能覆盖当前 Display 接口的测试画面。"""
    display.show_lines(["ST7789", "LCD TEST", "READY"], big=True)
    time.sleep(delay)

    # 重复颜色故意保留，用来检查颜色顺序不会被去重。
    display.show_color_order(["red", "red", "blue", "yellow"], quality=95)
    time.sleep(delay)

    display.show_status("RUN", sign=1, quality=88)
    time.sleep(delay)

    display.show_status("RUN", sign=2, quality=76)
    time.sleep(delay)

    display.show_lines(["LCD TEST", "PASS"], big=True)
    time.sleep(delay)


def main():
    args = parse_args()
    if args.delay < 0:
        raise SystemExit("--delay 不能小于 0")
    if args.cycles < 0:
        raise SystemExit("--cycles 不能小于 0")

    display = Display()
    try:
        cycle = 0
        while args.cycles == 0 or cycle < args.cycles:
            cycle += 1
            print(f"[test_lcd] cycle {cycle}")
            show_test_cycle(display, args.delay)
    except KeyboardInterrupt:
        print("\n[test_lcd] stopped by user")
    finally:
        display.close()
        print("[test_lcd] finished")


if __name__ == "__main__":
    main()
