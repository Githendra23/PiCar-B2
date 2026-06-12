from classes.ServoController import ServoController

class Tourelle:
    def __init__(self, controller : ServoController):
        self.CHANNEL_PAN = 1 # horizontal
        self.CHANNEL_TILT = 2 # vertical

        self.ANGLE_MAX = 180
        self.ANGLE_MIN = 0
        self.CENTER_PAN = 97
        self.CENTER_TILT = 96
        
        self.controller = controller
        self.controller.add_servo(self.CHANNEL_PAN)
        self.controller.add_servo(self.CHANNEL_TILT)
        self.reset()
        
    def pan(self, angle):
        if (angle >= self.ANGLE_MIN and angle <= self.ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL_PAN, angle)
        else:
            ValueError("Tourelle fonction pan - Hors de portée")

    def tilt(self, angle):
        if (angle >= self.ANGLE_MIN and angle <= self.ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL_TILT, angle)
        else:
            ValueError("Tourelle fonction tilt - Hors de portée")

    def getAngleMax(self):
        return self.ANGLE_MAX

    def getAngleMin(self):
        return self.ANGLE_MIN

    def getCenterPan(self):
        return self.CENTER_PAN

    def getCenterTilt(self):
        return self.CENTER_TILT

    def reset(self):
        self.controller.set_angle(self.CHANNEL_PAN, self.CENTER_PAN)
        self.controller.set_angle(self.CHANNEL_TILT, self.CENTER_TILT)