import spidev
import threading
import numpy
import time


class BandeLed(threading.Thread):
    """
    Classe mere : pilote WS2812/SK6812 sur SPI.
    Contient tout le code commun (bus SPI, ecriture des pixels, couleurs...).
    Les classes filles (FeuxArriere, LEDDroitBas, LEDGaucheBas) heritent de
    cette classe et n'ajoutent que leurs methodes specifiques (leurs zones).
    """

    def __init__(self, count=8, bright=255, sequence='GRB', bus=0, device=0,
                 *args, **kwargs):
        self.__set_led_type(sequence)
        self.__set_led_count(count)
        self.set_led_brightness(bright)
        self.__led_begin(bus, device)
        self.lightMode = 'none'
        self.colorBreathR = 0
        self.colorBreathG = 0
        self.colorBreathB = 0
        self.breathSteps = 10
        self.set_all_led_color(0, 0, 0)
        super(BandeLed, self).__init__(*args, **kwargs)
        self._flag = threading.Event()
        self._flag.clear()

    def __led_begin(self, bus=0, device=0):
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

    def __set_led_count(self, count):
        self.led_count = count
        self.led_color = [0, 0, 0] * self.led_count
        self.led_original_color = [0, 0, 0] * self.led_count

    def __set_led_type(self, rgb_type):
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

    def set_led_brightness(self, brightness):
        self.led_brightness = brightness

        for i in range(self.led_count):
            self.set_led_rgb_data(i, self.led_original_color)

    def __set_ledpixel(self, index, r, g, b):
        p = [0, 0, 0]
        p[self.led_red_offset] = round(r * self.led_brightness / 255)
        p[self.led_green_offset] = round(g * self.led_brightness / 255)
        p[self.led_blue_offset] = round(b * self.led_brightness / 255)
        self.led_original_color[index * 3 + self.led_red_offset] = r
        self.led_original_color[index * 3 + self.led_green_offset] = g
        self.led_original_color[index * 3 + self.led_blue_offset] = b

        for i in range(3):
            self.led_color[index * 3 + i] = p[i]

    def set_led_color_data(self, index, r, g, b):
        self.__set_ledpixel(index, r, g, b)

    def set_led_rgb_data(self, index, color):
        self.__set_ledpixel(index, color[0], color[1], color[2])

    def set_all_led_color_data(self, r, g, b):
        for i in range(self.led_count):
            self.set_led_color_data(i, r, g, b)

    def set_all_led_rgb_data(self, color):
        for i in range(self.led_count):
            self.set_led_rgb_data(i, color)

    def set_all_led_color(self, r, g, b):
        for i in range(self.led_count):
            self.set_led_color_data(i, r, g, b)

        self.show()

    def set_all_led_rgb(self, color):
        for i in range(self.led_count):
            self.set_led_rgb_data(i, color)

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

    def write_ws2812_numpy4(self):
        d = numpy.array(self.led_color).ravel()
        tx = numpy.zeros(len(d) * 4, dtype=numpy.uint8)

        for ibit in range(4):
            tx[3 - ibit::4] = ((d >> (2 * ibit + 1)) & 1) * 0x60 \
                + ((d >> (2 * ibit + 0)) & 1) * 0x06 + 0x88

        if self.led_init_state != 0:
            if self.bus == 0:
                self.spi.xfer(tx.tolist(), int(4 / 1.25e-6))
            else:
                self.spi.xfer(tx.tolist(), int(4 / 1.0e-6))

    def show(self, mode=1):
        if mode == 1:
            self.write_ws2812_numpy8()
        else:
            self.write_ws2812_numpy4()

    def wheel(self, pos):
        if pos < 85:
            return [(255 - pos * 3), (pos * 3), 0]
        elif pos < 170:
            pos = pos - 85
            return [0, (255 - pos * 3), (pos * 3)]
        else:
            pos = pos - 170
            return [(pos * 3), 0, (255 - pos * 3)]

    def hsv2rgb(self, h, s, v):
        h = h % 360
        rgb_max = round(v * 2.55)
        rgb_min = round(rgb_max * (100 - s) / 100)
        i = round(h / 60)
        diff = round(h % 60)
        rgb_adj = round((rgb_max - rgb_min) * diff / 60)

        if i == 0:
            r, g, b = rgb_max, rgb_min + rgb_adj, rgb_min
        elif i == 1:
            r, g, b = rgb_max - rgb_adj, rgb_max, rgb_min
        elif i == 2:
            r, g, b = rgb_min, rgb_max, rgb_min + rgb_adj
        elif i == 3:
            r, g, b = rgb_min, rgb_max - rgb_adj, rgb_max
        elif i == 4:
            r, g, b = rgb_min + rgb_adj, rgb_min, rgb_max
        else:
            r, g, b = rgb_max, rgb_min, rgb_max - rgb_adj

        return [r, g, b]

    def resume(self):
        self._flag.set()

    def setLed(self, led_num, colour=[255, 255, 255], brightness=255):
        self.led_brightness = brightness
        self.set_led_color_data(led_num, colour[0], colour[1], colour[2])
        self.show()

    def setZone(self, indices, colour=[255, 255, 255], brightness=255):
        self.led_brightness = brightness

        for led_num in indices:
            self.set_led_rgb_data(led_num, colour)

        self.show()

    def off(self, indices=None):
        if indices is None:
            self.set_all_led_rgb([0, 0, 0])
        else:
            self.setZone(indices, [0, 0, 0], 255)