from classes.ServoController import ServoController

class Roues:
    def __init__(self, controller: ServoController):
        self.CHANNEL = 0
        self.ANGLE_MIN = 0
        self.ANGLE_MAX = 130
        self.ANGLE_CENTER = 90
        
        self.controller = controller
        self.controller.add_servo(self.CHANNEL)
        self.reset()
    
    def turn(self, angle):
        if (angle >= self.ANGLE_MIN and angle <= self.ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL, angle)
        else:
            ValueError("Roues fonction turn - Angle hors de portée")

    def getAngleMin(self):
        return self.ANGLE_MIN

    def getAngleMax(self):
        return self.ANGLE_MAX

    def getAngleCenter(self):
        return self.ANGLE_CENTER

    def reset(self):
        self.controller.set_angle(self.CHANNEL, self.ANGLE_CENTER)