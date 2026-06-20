import numpy
import spidev
import threading
import time

class FeuxArriere(threading.Thread):
    def __init__(self, count = 8, bright = 255, sequence='GRB', bus = 0, device = 0, *args, **kwargs):
        self.set_led_type(sequence)
        self.set_led_count(count)
        self.set_led_brightness(bright)
        self.led_begin(bus, device)
        self.lightMode = 'none'
        self.colorBreathR = 0
        self.colorBreathG = 0
        self.colorBreathB = 0
        self.breathSteps = 10
        #self.spi_gpio_info()
        self.set_all_led_color(0,0,0)
        super(FeuxArriere, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.clear()
    
    def led_begin(self, bus = 0, device = 0):
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

    def breathProcessing(self):
        while self.lightMode == 'breath':
            for i in range(0,self.breathSteps):
                if self.lightMode != 'breath':
                    break
                self.set_all_led_color(self.colorBreathR*i/self.breathSteps, self.colorBreathG*i/self.breathSteps, self.colorBreathB*i/self.breathSteps)
                #self.show()
                time.sleep(0.03)
            for i in range(0,self.breathSteps):
                if self.lightMode != 'breath':
                    break
                self.set_all_led_color(self.colorBreathR-(self.colorBreathR*i/self.breathSteps), self.colorBreathG-(self.colorBreathG*i/self.breathSteps), self.colorBreathB-(self.colorBreathB*i/self.breathSteps))
                #self.show()
                time.sleep(0.03)
                
    def policeProcessing(self):
        while self.lightMode == 'police':
            for i in range(0,3):
                self.set_all_led_color_data(0,0,255)
                self.show()
                time.sleep(0.05)
                self.set_all_led_color_data(0,0,0)
                self.show()
                time.sleep(0.05)
            if self.lightMode != 'police':
                break
            time.sleep(0.1)
            for i in range(0,3):
                self.set_all_led_color_data(255,0,0)
                self.show()
                time.sleep(0.05)
                self.set_all_led_color_data(0,0,0)
                self.show()
                time.sleep(0.05)
            time.sleep(0.1)
            
            
    def lightChange(self):
        if self.lightMode == 'none':
            self.pause()
        elif self.lightMode == 'police':
            self.policeProcessing()
        elif self.lightMode == 'breath':
            self.breathProcessing()    
    
    def run(self):
        while 1:
            self.__flag.wait()
            self.lightChange()
            pass
        
    def setLed(self, led_num, colour = [255, 255, 255], brightness = 255):
        self.led_brightness = brightness
        self.set_led_rgb_data(led_num, colour)
        self.show()
    
    # Pour allumer toutes les leds arrières avec une couleur donnée et une luminosité donnée.
    def setBackLeds(self, colour = [255, 255, 255], brightness = 255):
        BACK_LED = [8, 9, 10, 11, 12, 13]
        
        for led_num in BACK_LED:
            self.setLed(led_num, colour, brightness)
            
        self.show()
    
    
    def off(self):
        self.setBackLeds([0, 0, 0], 255)
            
        
    # Pour avoir un effet de clignotement des leds arrières,
    # on allume les leds arrières avec une couleur donnée pendant un certain temps,
    # puis on les éteint pendant le même temps.
    def blinkAlert(self) :
        color = [255, 0, 0]
        delay = 0.125
        self.setBackLeds(color,255)
        time.sleep(delay)
        self.setBackLeds([0, 0, 0],255)
        time.sleep(delay)

    # Pour avoir un effet de clignotement séquentiel des leds arrières,
    # on allume les leds par couple (gauche/droite) avec un délai entre chaque couple.
    def sequentialWarning(self) :
        COUPLES_LED = [(8,13), (9,12), (10,11)]
        
        color = [255,128,0]

        for left, right in COUPLES_LED:
            self.setLed(left, color, 255)
            self.setLed(right, color, 255)
            time.sleep(0.15)

        self.setBackLeds([0,0,0],255)
        time.sleep(0.2)


        
if __name__ == '__main__':

    feuxArriere = FeuxArriere()

    try:
        if feuxArriere.check_spi_state() != 0:
            while True :
                feuxArriere.sequentialWarning()
        else:
            print("Fin du main()")
            
    except KeyboardInterrupt:
        print("Interruption via le clavier.")

    finally :
        feuxArriere.led_close()