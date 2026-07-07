import time
from BandeLED import BandeLED


class FeuxArriere(BandeLED):
    """Feux arriere du robot : leds 8 a 13, avec effets d'alerte."""

    BACK_LED = [8, 9, 10, 11, 12, 13]
    COUPLES_LED = [(8, 13), (9, 12), (10, 11)]

    def setBackLeds(self, colour=[255, 255, 255], brightness=255):
        """Allume tous les feux arriere."""
        self.setZone(self.BACK_LED, colour, brightness)

    def setZone(self, LEDS, color, brightness) :
        for led in LEDS :
            super().setLed(led,color, brightness)

    def off(self):
        """Eteint les feux arriere."""
        self.setZone(self.BACK_LED, [0, 0, 0], 255)

    def blinkAlert(self):
        """Clignotement rouge (alerte)."""
        color = [255, 0, 0]
        delay = 0.125
        self.setBackLeds(color, 255)
        time.sleep(delay)
        self.setBackLeds([0, 0, 0], 255)
        time.sleep(delay)

    def sequentialLeftOn(self, color) :
        LEDS = [8,9,10]
        
        for left in LEDS:
            super().setLed(left, color, 255)
            time.sleep(0.1)
    
    def sequentialRightOn(self, color) :
        LEDS = [13,12,11]
        
        for right in LEDS:
            super().setLed(right, color, 255)
            time.sleep(0.1)
        
    def sequentialOn(self, color) :
        COUPLES_LED = [(8,13), (9,12), (10,11)]
        
        for left, right in COUPLES_LED:
            super().setLed(left, color, 255)
            super().setLed(right, color, 255)
            time.sleep(0.1)

    def close(self) :
        self.off()
        self.led_close()
        
if __name__ == '__main__':
    try:
        feuxArriere = FeuxArriere(14, 255)
        if feuxArriere.check_spi_state() != 0:
            while True :
                color = [255,128,0]
                # feuxArriere.sequentialLeftOn(color)
                # feuxArriere.sequentialRightOn(color)
                feuxArriere.sequentialOn(color)
                time.sleep(1)
                feuxArriere.off()
                time.sleep(1)
        else:
            print("Fin du main()")
    except KeyboardInterrupt:
        print("Interruption via le clavier.")

    finally :
        feuxArriere.close()