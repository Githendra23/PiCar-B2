from classes.ServoController import ServoController

class Tourelle:
    def __init__(self, controller : ServoController):
        self.CHANNEL_PAN = 1 # horizontal
        self.CHANNEL_TILT = 2 # vertical
        
        self.controller = controller
        self.controller.add_servo(self.CHANNEL_PAN)
        self.controleler.add_servo(self.CHANNEL_TILT)
        
    def pan(self, angle):
        ANGLE_MAX = 180
        ANGLE_MIN = 0

        if (angle >= ANGLE_MIN and angle <= ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL_PAN, angle)

    def tilt(self, angle):
        ANGLE_MAX = 180
        ANGLE_MIN = 0

        if (angle >= ANGLE_MIN and angle <= ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL_TILT, angle)

    def reset(self):
        self.controller.set_angle(self.CHANNEL_PAN, 97)
        self.controller.set_angle(self.CHANNEL_TILT, 96)