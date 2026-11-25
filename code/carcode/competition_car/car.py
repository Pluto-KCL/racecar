"""基于成品 LOBOROBOT/PCA9685 逻辑的硬件适配层。"""

import time

try:
    import smbus
    import RPi.GPIO as GPIO
except ImportError:  # 允许在电脑上做语法和视觉回放测试
    smbus = None
    GPIO = None

from config import CFG


class Car:
    def __init__(self):
        self.ready = smbus is not None and GPIO is not None
        self.bus = smbus.SMBus(1) if self.ready else None
        self.address = CFG.pwm_address
        self.channels = CFG.motor_channels
        if self.ready:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(CFG.ultrasonic_trigger, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(CFG.ultrasonic_echo, GPIO.IN)
            GPIO.setup(25, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(24, GPIO.OUT, initial=GPIO.LOW)
            self._write(0x00, 0x00)
            self._set_frequency(50)

    def _write(self, register, value):
        self.bus.write_byte_data(self.address, register, value & 0xFF)

    def _set_frequency(self, frequency):
        prescale = int(25000000 / 4096 / frequency - 1)
        old = self.bus.read_byte_data(self.address, 0x00)
        self._write(0x00, (old & 0x7F) | 0x10)
        self._write(0xFE, prescale)
        self._write(0x00, old)
        time.sleep(0.005)
        self._write(0x00, old | 0x80)

    def _pwm(self, channel, duty):
        duty = max(0, min(100, float(duty)))
        value = int(duty * 4095 / 100)
        register = 0x06 + 4 * channel
        self._write(register, 0)
        self._write(register + 1, 0)
        self._write(register + 2, value & 0xFF)
        self._write(register + 3, value >> 8)

    def _level(self, channel, value):
        self._pwm(channel, 100 if value else 0)

    def _motor(self, index, value):
        if CFG.motor_invert[index]:
            value = -value
        value = max(-100, min(100, float(value)))
        pwm = self.channels[index]
        self._pwm(pwm, abs(value))
        if index == 0:
            a, b = 2, 1
            self._level(a, 0 if value >= 0 else 1)
            self._level(b, 1 if value >= 0 else 0)
        elif index == 1:
            a, b = 3, 4
            self._level(a, 1 if value >= 0 else 0)
            self._level(b, 0 if value >= 0 else 1)
        elif index == 2:
            a, b = 8, 7
            self._level(a, 1 if value >= 0 else 0)
            self._level(b, 0 if value >= 0 else 1)
        else:
            GPIO.output(25, 0 if value >= 0 else 1)
            GPIO.output(24, 1 if value >= 0 else 0)

    def set_motors(self, front_left, rear_left, rear_right, front_right):
        values = (front_left, rear_left, rear_right, front_right)
        if not self.ready:
            return
        for index, value in enumerate(values):
            self._motor(index, value)

    def stop(self):
        if self.ready:
            for channel in self.channels:
                self._pwm(channel, 0)

    def forward(self, speed):
        self.set_motors(speed, speed, speed, speed)

    def strafe(self, speed):
        self.set_motors(-speed, speed, -speed, speed)

    def rotate(self, speed):
        self.set_motors(-speed, -speed, speed, speed)

    def set_servo_angle(self, channel, angle):
        """沿用成品 LOBOROBOT 的 50Hz 舵机角度换算。"""
        if not self.ready:
            return
        angle = max(CFG.servo_min_angle, min(CFG.servo_max_angle, float(angle)))
        pulse = int(4096 * ((angle * 11) + 500) / 20000)
        register = 0x06 + 4 * channel
        self._write(register, 0)
        self._write(register + 1, 0)
        self._write(register + 2, pulse & 0xFF)
        self._write(register + 3, pulse >> 8)

    def distance_cm(self):
        if not self.ready:
            return None
        GPIO.output(CFG.ultrasonic_trigger, GPIO.LOW)
        time.sleep(0.000002)
        GPIO.output(CFG.ultrasonic_trigger, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(CFG.ultrasonic_trigger, GPIO.LOW)
        start = time.monotonic()
        while GPIO.input(CFG.ultrasonic_echo) == GPIO.LOW:
            if time.monotonic() - start > 0.03:
                return None
        pulse_start = time.monotonic()
        while GPIO.input(CFG.ultrasonic_echo) == GPIO.HIGH:
            if time.monotonic() - pulse_start > 0.03:
                return None
        return (time.monotonic() - pulse_start) * 17150

    def close(self):
        self.stop()
        if self.ready:
            GPIO.cleanup()
