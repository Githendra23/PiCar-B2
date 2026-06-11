import time
import smbus

class CapteurLumiere(object):
    def __init__(self):
        self.cmd = 0x84
        self.bus = smbus.SMBus(1)
        self.address = 0x48
    
    def analogRead(self, channel):
        value = self.bus.read_byte_data(
            self.address,
            self.cmd | (((channel << 2 | channel >> 1) & 0x07) << 4)
        )
        return value


if __name__ == "__main__":
    adc = CapteurLumiere()

    while True:
        adc_value = adc.analogRead(1)
        print(f"Light Tracking Value: {adc_value}")
        time.sleep(0.5)