from gpiozero import LED

class LedHAT:
    def __init__(self):
        self.ledsHAT = [LED(9), LED(25), LED(11)]

    def all_off(self):
        for led in self.ledsHAT:
            led.off()

    def apply(self, led_index = [0, 0, 0]):
        for i in range(len(self.ledsHAT)):
            if led_index[i] == 1:
                self.ledsHAT[i].on()
            elif led_index[i] == 0:
                self.ledsHAT[i].off()
            else:
                raise ValueError(f"LedHAT: Mauvaise valeur pour la LED {i} : {led_index[i]}")

if __name__ == "__main__":
    led = LedHAT()
    led.on([1, 0, 1])