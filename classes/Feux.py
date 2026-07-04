import self_components.FeuxArriere as FeuxArriere
import self_components.FeuxAvant as FeuxAvant

import time

BLINK_DELAY = 0.1
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

    def blinkRight(self) :
        self.feuxAvant.switch(17)
        self.feuxAvant.switch(18)

        self.feuxArriere.sequentialRightOn(YELLOW)

        self.feuxAvant.off()
        self.feuxArriere.off()

    def close(self) :
        self.feuxArriere.close()
        self.feuxAvant.off()



if __name__ == "__main__" :
    feux = Feux()
    try :
        while True :
            feux.blinkLeft()
            time.sleep(0.5)
            feux.blinkRight()
            time.sleep(0.5)
    except KeyboardInterrupt :
        print("Interruption via le clavier.")
    finally :
        feux.close()