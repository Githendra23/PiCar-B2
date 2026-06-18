#!/usr/bin/env/python
import time
import board
import busio
from adafruit_bus_device.i2c_device import I2CDevice


buffer = [1]
# Define constants
Vref = 8.4
WarningThreshold = 6.75
R15 = 3000
R17 = 1000
DivisionRatio = R17 / (R15 + R17)

class Batterie :
    def __init__(self) :
        i2c = busio.I2C(board.SCL, board.SDA)
        # ADS7830 adress 0x48
        self.device = I2CDevice(i2c, 0x48)

        #Define the ADC channel and command.
        cmd = 0x84
        channel = 0
        self.control_byte = cmd | (((channel << 2 | channel >> 1) & 0x07) << 4)
    
    def getPercentage(self) :
        self.device.write_then_readinto(bytes([self.control_byte]), buffer)
        adcValue = buffer[0]
        print(str(adcValue))
        A0Voltage = (adcValue / 255) * 5
        ActualBatteryVoltage = A0Voltage / DivisionRatio
        batteryPercentage = (ActualBatteryVoltage - WarningThreshold) / (Vref - WarningThreshold) * 100
        return batteryPercentage


if __name__ == "__main__" :
    batterie = Batterie()
    while True:
        pcnt = batterie.getPercentage()
        print(f"Current battery level: {pcnt:.2f} %")

        # Battery level warning judgment
        if pcnt < 20:
            print("Batterie faible ! Branchez l'alimentation.")
        time.sleep(0.5)
