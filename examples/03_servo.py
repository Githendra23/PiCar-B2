#!/usr/bin/env/python3
'''
 SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Import the PCA9685 module. Available in the bundle and here:
#   https://github.com/adafruit/Adafruit_CircuitPython_PCA9685
# sudo pip3 install adafruit-circuitpython-motor
# sudo pip3 install adafruit-circuitpython-pca9685
'''
import time
from board import SCL, SDA
import busio
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685

class ServoController:
    def __init__(self, i2c_address=0x5f, frequency=50, min_pulse=500, max_pulse=2400, actuation_range=180):
        self.i2c = busio.I2C(SCL, SDA)
        self.pca = PCA9685(self.i2c, address=i2c_address)
        self.pca.frequency = frequency
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        self.actuation_range = actuation_range
        self.servos = {}  # Dictionnaire pour ranger les instances de servo

    def add_servo(self, channel, min_pulse=None, max_pulse=None, actuation_range=None):
        min_pulse = min_pulse if min_pulse is not None else self.min_pulse
        max_pulse = max_pulse if max_pulse is not None else self.max_pulse
        actuation_range = actuation_range if actuation_range is not None else self.actuation_range

        self.servos[channel] = servo.Servo(
            self.pca.channels[channel],
            min_pulse=min_pulse,
            max_pulse=max_pulse,
            actuation_range=actuation_range
        )

    def set_angle(self, channel, angle):
        if channel in self.servos:
            self.servos[channel].angle = angle
        else:
            raise ValueError(f"Aucun servo configuré sur le cannal {channel}.")

    def sweep(self, channel, start_angle=0, end_angle=180, step=1, delay=0.01):
        if channel not in self.servos:
            raise ValueError(f"Aucun servo configuré sur le cannal {channel}.")

        for angle in range(start_angle, end_angle + 1, step):
            self.set_angle(channel, angle)
            time.sleep(delay)

        time.sleep(0.5)

        for angle in range(end_angle, start_angle -1, -step):
            self.set_angle(channel, angle)
            time.sleep(delay)

        time.sleep(0.5)

    def test(self, channel):

        self.sweep(channel, start_angle=0, enf_angle=180)

if __name__ == "__main__":

    servo_controller = ServoController(i2c_address=0x5f)
    
    servo_controller.add_servo(channel=2)
    
    while True:
        servo_controller.test(channel=2)

