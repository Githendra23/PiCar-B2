import time
from BandeLED import BandeLED


class LEDDroitBas(BandeLED):
    FRONT_LED = [0, 1]
    BOTTOM_LED = [2, 3, 4]

    def setFront(self, colour=[255, 255, 255], brightness=255):
        self.setZone(self.FRONT_LED, colour, brightness)

    def setBottom(self, colour=[255, 255, 255], brightness=255):
        self.setZone(self.BOTTOM_LED, colour, brightness)


if __name__ == '__main__':
    try:
        ledDroitBas = LEDDroitBas()
        if ledDroitBas.check_spi_state() != 0:
            ledDroitBas.setBottom([255, 0, 0], 255)
            time.sleep(2)
    except KeyboardInterrupt:
        print("Interruption du programme via le clavier.")
    finally:
        ledDroitBas.led_close()