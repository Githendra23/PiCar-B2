import spidev
import threading  
import numpy
from numpy import sin, cos, pi
import time

class BandeLed(threading.Thread):
    def __init__(self):
        self.bus = 0
        self.device = 0

        self.LEDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

        self.set_led_type('GRB')
        self.set_led_count(len(self.LEDS))
        self.spi = spidev.SpiDev()
        self.set_all_led_brightness(0)
        self.led_begin(self.bus, self.device)
        self.lightMode = 'none'
        self.colorBreathR = 0
        self.colorBreathG = 0
        self.colorBreathB = 0
        self.breathSteps = 10
        self.set_all_led_rgb([0,0,0])
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
        self.set_all_led_rgb([0,0,0])
        self.spi.close()
    
    def set_led_count(self, count):
        self.led_count = count
        self.led_color = [0,0,0] * self.led_count
        self.led_original_color = [0,0,0] * self.led_count
    
    def set_led_type(self, rgb_type):
        try:
            led_type = ['RGB','RBG','GRB','GBR','BRG','BGR']
            led_type_offset = [0x06,0x09,0x12,0x21,0x18,0x24]
            index = led_type.index(rgb_type)
            self.led_red_offset = (led_type_offset[index]>>4) & 0x03
            self.led_green_offset = (led_type_offset[index]>>2) & 0x03
            self.led_blue_offset = (led_type_offset[index]>>0) & 0x03

            return index
        except ValueError:
            self.led_red_offset = 1
            self.led_green_offset = 0
            self.led_blue_offset = 2
            return -1
    
    def set_all_led_brightness(self, brightness):
        self.led_brightness = brightness

        for i in range(self.led_count):
            self.set_led_rgb_data(i, self.led_original_color)

    def set_led_brightness(self, led_num, brightness):
        self.led_brightness = brightness
        self.set_led_rgb_data(led_num, self.led_original_color)
            
    def set_ledpixel(self, index, r, g, b):
        p = [0,0,0]
        p[self.led_red_offset] = round(r * self.led_brightness / 255)
        p[self.led_green_offset] = round(g * self.led_brightness / 255)
        p[self.led_blue_offset] = round(b * self.led_brightness / 255)
        self.led_original_color[index*3+self.led_red_offset] = r
        self.led_original_color[index*3+self.led_green_offset] = g
        self.led_original_color[index*3+self.led_blue_offset] = b

        for i in range(3):
            self.led_color[index*3+i] = p[i] 
        
    def set_led_rgb_data(self, index, color):
        self.set_ledpixel(index, color[0], color[1], color[2])
        
    def set_led_rgb(self, index, color):
        self.set_led_rgb_data(index, color)   
        self.show()
            
    def set_all_led_rgb_data(self, color):
        for i in range(self.led_count):
            self.set_led_rgb_data(i, color)   
        
    def set_all_led_rgb(self, color):
        for i in range(self.led_count):
            self.set_led_rgb_data(i, color)

        self.show()
    
    def write_ws2812_numpy8(self):
        d = numpy.array(self.led_color).ravel()        #Converts data into a one-dimensional array
        tx = numpy.zeros(len(d)*8, dtype=numpy.uint8)  #Each RGB color has 8 bits, each represented by a uint8 type data

        for ibit in range(8):                          #Convert each bit of data to the data that the spi will send
            tx[7-ibit::8]=((d>>ibit)&1)*0x78 + 0x80    #T0H=1,T0L=7, T1H=5,T1L=3   #0b11111000 mean T1(0.78125us), 0b10000000 mean T0(0.15625us)

        if self.led_init_state != 0:
            if self.bus == 0:
                self.spi.xfer(tx.tolist(), int(8/1.25e-6))         #Send color data at a frequency of 6.4Mhz
            else:
                self.spi.xfer(tx.tolist(), int(8/1.0e-6))          #Send color data at a frequency of 8Mhz
        
    def write_ws2812_numpy4(self):
        d=numpy.array(self.led_color).ravel()
        tx=numpy.zeros(len(d)*4, dtype=numpy.uint8)

        for ibit in range(4):
            tx[3-ibit::4]=((d>>(2*ibit+1))&1)*0x60 + ((d>>(2*ibit+0))&1)*0x06 + 0x88

        if self.led_init_state != 0:
            if self.bus == 0:
                self.spi.xfer(tx.tolist(), int(4/1.25e-6))         
            else:
                self.spi.xfer(tx.tolist(), int(4/1.0e-6))       
        
    def show(self, mode = 1):
        if mode == 1:
            write_ws2812 = self.write_ws2812_numpy8
        else:
            write_ws2812 = self.write_ws2812_numpy4
        write_ws2812()

    def police(self):
        self.lightMode = 'police'
        self.resume()

    def breath(self, R_input, G_input, B_input):
        self.lightMode = 'breath'
        self.colorBreathR = R_input
        self.colorBreathG = G_input
        self.colorBreathB = B_input
        self.resume()
            
    def resume(self):
        self.__flag.set()

    def breathProcessing(self):
        while self.lightMode == 'breath':
            for i in range(0,self.breathSteps):
                if self.lightMode != 'breath':
                    break

                self.set_all_led_rgb([self.colorBreathR*i/self.breathSteps, self.colorBreathG*i/self.breathSteps, self.colorBreathB*i/self.breathSteps])
                #self.show()
                time.sleep(0.03)

            for i in range(0,self.breathSteps):
                if self.lightMode != 'breath':
                    break

                self.set_all_led_rgb([self.colorBreathR-(self.colorBreathR*i/self.breathSteps), self.colorBreathG-(self.colorBreathG*i/self.breathSteps), self.colorBreathB-(self.colorBreathB*i/self.breathSteps)])
                #self.show()
                time.sleep(0.03)
                
    def policeProcessing(self):
        while self.lightMode == 'police':
            for i in range(0,3):
                self.set_all_led_rgb_data([0,0,255])
                self.show()
                time.sleep(0.05)
                self.set_all_led_rgb_data([0,0,0])
                self.show()
                time.sleep(0.05)

            if self.lightMode != 'police':
                break

            time.sleep(0.1)

            for i in range(0,3):
                self.set_all_led_rgb_data([255,0,0])
                self.show()
                time.sleep(0.05)
                self.set_all_led_rgb_data([0,0,0])
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
        
    def set_led(self, led_num, colour = [255, 255, 255], brightness = 255):
        self.led_brightness = brightness
        self.set_led_rgb(led_num, colour)
        self.show()
        
    def set_back_leds(self, colour = [255, 255, 255], brightness = 255):
        BACK_LED = [8, 9, 10, 11, 12, 13]
        
        for led_num in BACK_LED:
            self.set_led(led_num, colour, brightness)
            
        self.show()
        
    def set_front_leds(self, colour = [255, 255, 255], brightness = 255):
        FRONT_LED = [0, 1]
        
        for led_num in FRONT_LED:
            self.set_led(led_num, colour, brightness)
            
        self.show()
        
    def set_bottomLeft_leds(self, colour = [255, 255, 255], brightness = 255):
        BOTTOM_LEFT_LED = [5, 6, 7]
        
        for led_num in BOTTOM_LEFT_LED:
            self.set_led(led_num, colour, brightness)
            
        self.show()
        
    def set_bottomRight_leds(self, colour = [255, 255, 255], brightness = 255):
        BOTTOM_RIGHT_LED = [2, 3, 4]
        
        for led_num in BOTTOM_RIGHT_LED:
            self.set_led(led_num, colour, brightness)
            
        self.show()
        
if __name__ == '__main__':
    import os
    
    print("spidev version is ", spidev.__version__)
    print("spidev device as show:")
    os.system("ls /dev/spi*")

    led = BandeLed()

    try:
        if led.check_spi_state() != 0:
            led.set_back_leds([255, 0, 0],255)
            time.sleep(1)

            led.set_back_leds([0, 0, 255], 255)
            time.sleep(1)
        else:
            led.led_close()
            
    except KeyboardInterrupt:
        led.led_close()