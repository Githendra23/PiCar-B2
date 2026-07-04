import time
from BandeLed import BandeLed


class LEDGaucheBas(BandeLed):
    FRONT_LED = [0, 1]
    BOTTOM_LED = [5, 6, 7]

    def setFront(self, colour=[255, 255, 255], brightness=255):
        self.setZone(self.FRONT_LED, colour, brightness)

    def setBottom(self, colour=[255, 255, 255], brightness=255):
        self.setZone(self.BOTTOM_LED, colour, brightness)


if __name__ == '__main__':
    try:
        ledGaucheBas = LEDGaucheBas()
        if ledGaucheBas.check_spi_state() != 0:
            ledGaucheBas.setFront([0, 255, 0], 255)
            ledGaucheBas.setBottom([0, 0, 255], 255)
            time.sleep(2)
    except KeyboardInterrupt:
        print("Interruption du programme via le clavier.")
    finally:
        ledGaucheBas.led_close()