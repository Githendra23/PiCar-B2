import spidev
import numpy
import time

class BandeLED(threading.Thread):
    def __init__(self):
        self.bus = 0
        self.device = 0

        self.LEDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

        self.set_led_type('GRB')
        self.set_led_count(len(self.LEDS))
        self.spi = spidev.SpiDev()
        self.led_brightness = 0
        self.led_begin(self.bus, self.device)
        self.set_all_led_rgb([0, 0, 0])

    def led_begin(self, bus=0, device=0):
        self.bus = bus
        self.device = device

        try:
            self.spi = spidev.SpiDev()
            self.spi.open(self.bus, self.device)
            self.spi.mode = 0
            self.led_init_state = 1
        except OSError:
            print("Please check the configuration in /boot/firmware/config.txt.")

            if self.bus == 0:
                print("You can turn on the 'SPI' in 'Interface Options' by using 'sudo raspi-config'.")
                print("Or make sure that 'dtparam=spi=on' is not commented, then reboot the Raspberry Pi. Otherwise spi0 will not be available.")
            else:
                print("Please add 'dtoverlay=spi{}-2cs' at the bottom of the /boot/firmware/config.txt, then reboot the Raspberry Pi. otherwise spi{} will not be available.".format(self.bus, self.bus))

            self.led_init_state = 0

    def check_spi_state(self):
        return self.led_init_state

    def led_close(self):
        self.set_all_led_rgb([0, 0, 0])
        self.spi.close()

    def set_led_count(self, count):
        self.led_count = count
        self.led_color = [0, 0, 0] * self.led_count
        self.led_original_color = [0, 0, 0] * self.led_count

    def set_led_type(self, rgb_type):
        try:
            led_type = ['RGB', 'RBG', 'GRB', 'GBR', 'BRG', 'BGR']
            led_type_offset = [0x06, 0x09, 0x12, 0x21, 0x18, 0x24]
            index = led_type.index(rgb_type)
            
            self.led_red_offset = (led_type_offset[index] >> 4) & 0x03
            self.led_green_offset = (led_type_offset[index] >> 2) & 0x03
            self.led_blue_offset = (led_type_offset[index] >> 0) & 0x03

            return index
        except ValueError:
            self.led_red_offset = 1
            self.led_green_offset = 0
            self.led_blue_offset = 2
            return -1

    def set_ledpixel(self, index, r, g, b):
        p = [0, 0, 0]

        p[self.led_red_offset] = round(r * self.led_brightness / 255)
        p[self.led_green_offset] = round(g * self.led_brightness / 255)
        p[self.led_blue_offset] = round(b * self.led_brightness / 255)

        self.led_original_color[index * 3 + self.led_red_offset] = r
        self.led_original_color[index * 3 + self.led_green_offset] = g
        self.led_original_color[index * 3 + self.led_blue_offset] = b

        for i in range(3):
            self.led_color[index * 3 + i] = p[i]

    def set_led_rgb_data(self, index, color):
        self.set_ledpixel(index, color[0], color[1], color[2])

    def set_all_led_rgb(self, color):
        for i in range(self.led_count):
            self.set_ledpixel(i, color[0], color[1], color[2])

        self.show()

    def write_ws2812_numpy8(self):
        d = numpy.array(self.led_color).ravel()
        tx = numpy.zeros(len(d) * 8, dtype=numpy.uint8)

        for ibit in range(8):
            tx[7 - ibit::8] = ((d >> ibit) & 1) * 0x78 + 0x80

        if self.led_init_state != 0:
            if self.bus == 0:
                self.spi.xfer(tx.tolist(), int(8 / 1.25e-6))
            else:
                self.spi.xfer(tx.tolist(), int(8 / 1.0e-6))

    def show(self):
        self.write_ws2812_numpy8()

    def set_led(self, led_num, colour=[255, 255, 255], brightness=255):
        if led_num not in self.LEDS:
            raise ValueError(f"LED {led_num} inexistante. LED valides : {self.LEDS}")

        self.led_brightness = brightness
        self.set_led_rgb_data(led_num, colour)
        self.show()

    def set_back_leds(self, colour=[255, 255, 255], brightness=255):
        self.led_brightness = brightness

        for led_num in self.LEDS[8:14]:
            self.set_led_rgb_data(led_num, colour)

        self.show()

    def set_front_leds(self, colour=[255, 255, 255], brightness=255):
        self.led_brightness = brightness

        for led_num in self.LEDS[0:2]:
            self.set_led_rgb_data(led_num, colour)

        self.show()

    def set_bottomLeft_leds(self, colour=[255, 255, 255], brightness=255):
        self.led_brightness = brightness

        for led_num in self.LEDS[5:8]:
            self.set_led_rgb_data(led_num, colour)

        self.show()

    def set_bottomRight_leds(self, colour=[255, 255, 255], brightness=255):
        self.led_brightness = brightness

        for led_num in self.LEDS[2:5]:
            self.set_led_rgb_data(led_num, colour)

        self.show()


if __name__ == '__main__':
    import os

    print("spidev version is ", spidev.__version__)
    print("spidev device as show:")
    os.system("ls /dev/spi*")

    led = BandeLED()

    try:
        if led.check_spi_state() != 0:
            led.set_back_leds([255, 0, 0], 255)
            time.sleep(1)
            led.set_back_leds([0, 0, 255], 255)
            time.sleep(1)

            led.set_all_led_rgb([0, 0, 0])
            time.sleep(1)

            led.set_led(0, [255, 0, 0], 255)
            time.sleep(1)
            led.set_led(5, [0, 255, 0], 128)
            time.sleep(1)

            led.led_close()
        else:
            led.led_close()

    except KeyboardInterrupt:
        led.led_close()