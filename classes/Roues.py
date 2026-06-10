import ServoController

class Roues:
    def __innit__(self, controller: ServoController):
        self.CHANNEL = 0
        
        self.controller = controller
        self.controller.add_servo(self.CHANNEL)
        self.controller.set_angle(90)
    
    def turn(self, angle):
        ANGLE_MIN = 0
        ANGLE_MAX = 130
        
        if (angle >= ANGLE_MIN and angle <= ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL, angle)
            
    def reset(self):
        self.controller.set_angle(self.CHANNEL, 90)