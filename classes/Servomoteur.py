import time
from board import SCL, SDA
import busio
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685

# CONSTANTES POUR LES DIFFÉRENTS SERVOMOTEURS
DIRECTION = 0
TOURELLE_X_AXIS = 1
TOURELLE_Y_AXIS = 2


class Servomoteur():
    def __init__(self, channel):
        self.i2c = busio.I2C(SCL, SDA)
        self.pca = PCA9685(self.i2c, address=0x5f)
        self.pca.frequency = 50
        self.min_pulse = 500
        self.max_pulse = 2400
        self.actuation_range = 180

        self.servo = servo.Servo(
            self.pca.channels[channel],
            min_pulse=self.min_pulse,
            max_pulse=self.max_pulse,
            actuation_range=self.actuation_range
        )

    def setAngle(self, angle):
            self.servo.angle = angle
    
    def reset(self) :
         self.setAngle(90)

if __name__ == "__main__":
    servomoteur = Servomoteur(0)
    
    try :
        while True:
            servomoteur.setAngle(0);
            time.sleep(1)
            servomoteur.setAngle(180);
            time.sleep(1)
    except KeyboardInterrupt :
        print("Fin du programme via le terminal.")
    finally :
        servomoteur.reset()