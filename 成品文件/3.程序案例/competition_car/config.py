"""树莓派单机竞赛车参数。先架空测试，再在低速下标定。"""

from dataclasses import dataclass


@dataclass
class Config:
    # 摄像头
    camera_width: int = 640
    camera_height: int = 480
    camera_fps: int = 30
    camera_format: str = "RGB888"
    exposure_us: int = 12000
    roi_top: float = 0.52
    roi_bottom: float = 0.98

    # 黑色循迹线阈值。按现场光照调整
    line_gray_threshold: int = 85
    line_min_area: int = 180
    line_kp: float = 0.75
    line_kd: float = 0.18
    line_speed: float = 32.0
    line_max_correction: float = 28.0

    # 成品代码中 PCA9685 的电机通道
    motor_channels: tuple = (0, 5, 6, 11)
    motor_invert: tuple = (False, False, False, False)
    pwm_address: int = 0x40
    # 成品示例中的二维云台舵机通道。通道 10 水平，通道 9 俯仰。
    pan_servo_channel: int = 10
    tilt_servo_channel: int = 9
    pan_center: float = 90.0
    tilt_center: float = 50.0
    servo_min_angle: float = 0.0
    servo_max_angle: float = 180.0

    # 产品示例中的超声波 GPIO，使用 BCM 编号
    # 成品超声波示例使用 BCM GPIO20/21
    ultrasonic_trigger: int = 20
    ultrasonic_echo: int = 21
    obstacle_stop_cm: float = 25.0
    obstacle_clear_cm: float = 45.0

    # 启动按键、蜂鸣器。未安装时可设为 None
    start_button: int = 18
    buzzer: int = 11

    # 比赛动作时序，需要实车标定
    sign_turn_seconds: float = 0.65
    parking_reverse_seconds: float = 1.10
    parking_turn_seconds: float = 0.75
    parking_stop_seconds: float = 5.0

    # 多帧识别确认
    sign_confirm_frames: int = 3
    color_confirm_frames: int = 5
    parking_sign_confirm_frames: int = 4
    arrow_min_area: int = 900
    parking_sign_min_area: int = 900

    # 按赛题地图估计的阶段参数。实际距离需要在 4.5m x 3.0m 场地复测。
    obstacle_bypass_seconds: float = 1.20
    arrow_turn_seconds: float = 0.65
    parking_approach_speed: float = 22.0


CFG = Config()

# 兼容 camera_fixed.py 的配置命名
CAM_WIDTH = CFG.camera_width
CAM_HEIGHT = CFG.camera_height
CAM_FORMAT = CFG.camera_format
EXPOSURE_US = CFG.exposure_us
