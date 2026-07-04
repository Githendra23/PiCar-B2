import time
from BandeLed import BandeLed


class FeuxArriere(BandeLed):
    """Feux arriere du robot : leds 8 a 13, avec effets d'alerte."""

    BACK_LED = [8, 9, 10, 11, 12, 13]
    COUPLES_LED = [(8, 13), (9, 12), (10, 11)]

    def setBackLeds(self, colour=[255, 255, 255], brightness=255):
        """Allume tous les feux arriere."""
        self.setZone(self.BACK_LED, colour, brightness)

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

    def sequentialWarningsOn(self):
        """Allumage sequentiel par couples (effet balayage)."""
        color = [255, 128, 0]
        for left, right in self.COUPLES_LED:
            self.setLed(left, color, 255)
            self.setLed(right, color, 255)
            time.sleep(0.1)

    def sequentialWarnings(self):
        """Effet de warning sequentiel complet (balayage puis extinction)."""
        self.sequentialWarningsOn()
        self.setBackLeds([0, 0, 0], 255)
        time.sleep(0.3)


if __name__ == '__main__':
    try:
        feuxArriere = FeuxArriere(14, 255)
        if feuxArriere.check_spi_state() != 0:
            while True:
                feuxArriere.sequentialWarnings()
        else:
            print("Fin du main()")
    except KeyboardInterrupt:
        print("Interruption via le clavier.")
    finally:
        feuxArriere.off()
        feuxArriere.led_close()