import ServoController

import time

class Direction:
    def __init__(self):
        self.servo = ServoController.ServoController()

        self.CHANNEL = 0

        self.ANGLE_MIN = 0 # droite
        self.ANGLE_MAX = 130 # gauche
        self.ANGLE_CENTER = 90

        self.servo.add_servo(self.CHANNEL)
        self.reset()

    def turn(self, angle):
        if(angle < self.ANGLE_MIN) :
            angle = self.ANGLE_MIN
        elif(angle > self.ANGLE_MAX) :
            angle = self.ANGLE_MAX
        self.servo.set_angle(self.CHANNEL, angle)        

    def getAngleMin(self):
        return self.ANGLE_MIN

    def getAngleMax(self):
        return self.ANGLE_MAX

    def getAngleCenter(self):
        return self.ANGLE_CENTER

    def reset(self):
        self.servo.set_angle(self.CHANNEL, self.ANGLE_CENTER)


if __name__ == "__main__" :
    direction = Direction()
    try :
        while True :
            angle = int(input("Entrez un angle : "))
            direction.turn(angle)
            time.sleep(0.5)
    except KeyboardInterrupt :
        print("Fin du programme.")
        direction.reset()
