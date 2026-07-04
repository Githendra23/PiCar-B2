import self_components.FeuxArriere as FeuxArriere
import self_components.FeuxAvant as FeuxAvant

import time

BLINK_DELAY = 0.3
YELLOW = [255,128,0]

class Feux :
    def __init__(self) :
        self.feuxArriere = FeuxArriere.FeuxArriere()
        self.feuxAvant = FeuxAvant.FeuxAvant()

    def blinkLeft(self) :
        self.feuxAvant.switch(14)
        self.feuxAvant.switch(15)

        self.feuxArriere.sequentialLeftOn(YELLOW)

        self.feuxAvant.off()
        self.feuxArriere.off()

    def blinkAlert(self) :
        self.feuxArriere.blinkAlert()

    def blinkRight(self) :
        self.feuxAvant.switch(17)
        self.feuxAvant.switch(18)

        self.feuxArriere.sequentialRightOn(YELLOW)

        self.feuxAvant.off()
        self.feuxArriere.off()

    def close(self) :
        self.feuxArriere.close()
        self.feuxAvant.off()

    def warnings(self) :
        self.feuxAvant.switch(14)
        self.feuxAvant.switch(15)
        self.feuxAvant.switch(17)
        self.feuxAvant.switch(18)

        self.feuxArriere.sequentialOn(YELLOW)
        time.sleep(BLINK_DELAY)
        self.feuxAvant.off()
        self.feuxArriere.off()
        time.sleep(BLINK_DELAY)


if __name__ == "__main__" :
    feux = Feux()
    try :
        while True :
            feux.warnings()
    except KeyboardInterrupt :
        print("Interruption via le clavier.")
    finally :
        feux.close()