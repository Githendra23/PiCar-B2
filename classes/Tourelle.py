import time

import ServoController

ANGLE_MAX = 180
ANGLE_MIN = 0


class Tourelle:
    def __init__(self):
        self.CHANNEL_X_AXIS = 1 # horizontal
        self.CHANNEL_Y_AXIS = 2 # vertical
        
        self.controller = ServoController.ServoController()
        self.controller.add_servo(self.CHANNEL_X_AXIS)
        self.controller.add_servo(self.CHANNEL_Y_AXIS)
        
    def turn_x_axis(self, angle):
        if (angle >= ANGLE_MIN and angle <= ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL_X_AXIS, angle)
        else:
            ValueError("Tourelle rotation X - Angle hors de portée")


    def turn_y_axis(self, angle):
        if (angle >= ANGLE_MIN and angle <= ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL_Y_AXIS, angle)
        else:
            ValueError("Tourelle rotation Y - Angle hors de portée")


    def print_angle(self) :
        print(f"Angle X : ")
        print(f"Angle Y : ")

    def getAngleMax(self):
        return self.ANGLE_MAX

    def getAngleMin(self):
        return self.ANGLE_MIN

    def getCenterPan(self):
        return self.CENTER_PAN

    def getCenterTilt(self):
        return self.CENTER_TILT

    def reset(self):
        self.turn_x_axis(90)
        self.turn_y_axis(90)


if __name__ == "__main__" :
    tourelle = Tourelle()

    try :
        while True :
            x_angle = int(input("Entrez l'angle sur l'axe X : "))
            y_angle = int(input("Entrez l'angle sur l'axe Y : "))

            tourelle.turn_x_axis(x_angle)
            tourelle.turn_y_axis(y_angle)
            # tourelle.print_angle()
            time.sleep(2)
            tourelle.reset()
            
    except KeyboardInterrupt :
        print("Fin du programme.")
        tourelle.reset()
