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
    def __init__(self):
        self.i2c = busio.I2C(SCL, SDA)
        self.pca = PCA9685(self.i2c, address=0x5f)
        self.pca.frequency = 50
        self.min_pulse = 500
        self.max_pulse = 2400
        self.actuation_range = 180
        self.servos = {} # Dictionnaire pour ranger les instances de servo

    def add_servo(self, channel):
        self.servos[channel] = servo.Servo(
            self.pca.channels[channel],
            min_pulse=self.min_pulse,
            max_pulse=self.max_pulse,
            actuation_range=self.actuation_range
        )

    def set_angle(self, channel, angle):
        if channel in self.servos:
            self.servos[channel].angle = angle
            time.sleep(10)
            self.servos[channel].angle = None
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

        self.sweep(channel, start_angle=0, end_angle=180)

if __name__ == "__main__":

    servo_controller = ServoController()
    
    servo_controller.add_servo(channel=2)
    
    while True:
        servo_controller.test(channel=2)

