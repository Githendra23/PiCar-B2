import time

import Buzzer
import Direction
import Moteur
import Tourelle


class Robot :
    def __init__(self):
        self.buzzer = Buzzer.Buzzer()
        self.direction = Direction.Direction()
        self.moteur = Moteur.Moteur()
        self.tourelle = Tourelle.Tourelle()


    def drive(self, speed) :
        self.moteur.drive(speed)

    def reverse(self, speed) :
        self.moteur.reverse(speed)

    def stop(self) :
        self.moteur.stop()

    def turnTourelleXAxis(self, angle) :
        self.tourelle.turn_x_axis(angle)
    
    def turnTourelleYAxis(self, angle) :
        self.tourelle.turn_y_axis(angle)

if __name__ == "__main__" :
    try :
        pass
    except KeyboardInterrupt :
        pass