import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import motor

import sys

# motor_EN_A: Pin7  |  motor_EN_B: Pin11
# motor_A:  Pin8,Pin10    |  motor_B: Pin13,Pin12

VMAX = 100

MOTOR_M1_IN1 =  15      #Define the positive pole of M1
MOTOR_M1_IN2 =  14      #Define the negative pole of M1

Dir_forward   = 0
Dir_backward  = 1

pwn_A = 0
pwm_B = 0

def map(x,in_min,in_max,out_min,out_max):
  return (x - in_min)/(in_max - in_min) *(out_max - out_min) + out_min


#def setup():
i2c = busio.I2C(SCL, SDA)
# Create a simple PCA9685 class instance.
#  pwm_motor.channels[7].duty_cycle = 0xFFFF
pwm_motor = PCA9685(i2c, address=0x5f) #default 0x40
pwm_motor.frequency = 50

motor1 = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1],pwm_motor.channels[MOTOR_M1_IN2] )
motor1.decay_mode = (motor.SLOW_DECAY)

def check_speed(vitesse) :
    if(vitesse > 100) :
        vitesse = 100
    elif(vitesse < 0) :
        vitesse = 0
    return vitesse


def progress_start(speed) :
    speed = check_speed(speed)
    for i in range(speed) :
        m1.moteur.throttle = map(i,0,100,0,1.0)
        time.sleep(0.05)


class Moteur:

    def __init__(self, moteur):
        self.moteur = moteur

    # Pour avancer
    def avancer(self, vitesse):
        vitesse = check_speed(vitesse)
        print(f"Le moteur avance ! Vitesse : {vitesse}")
        self.moteur.throttle = map(vitesse, 0, 100, 0, 1.0)

    # Pour reculer
    def reculer(self, vitesse):
      vitesse = check_speed(vitesse)
      print(f"Le moteur recule ! Vitesse : {vitesse}")
      self.moteur.throttle = -map(vitesse, 0, 100, 0, 1.0)
 
    # Arrêter le moteur
    def stop(self):
        print("Le moteur est à l'arrêt !")
        self.moteur.throttle = 0
    
    # Déconnecter le moteur
    def destroy(self):
        print("Destruction du moteur.")
        self.stop()
        pwm_motor.deinit()

    # INUTILE, ABÎME LA MÉCANIQUE SUR LE LONG TERME => A UTILISER LORSQUE
    # LE DIFFÉRENTIEL N'EST PAS RELIÉ AUX ROUES !!
    # METTRE UN RÉDUCTEUR DE COUPLE ÉLECTRONIQUE (TC ?)
    def launch_control(self) :
        print(f"LAUNCH CONTROL ! Vitesse : {100}")
        while True :
            self.moteur.throttle = 1.0
            time.sleep(0.1)

m1 = Moteur(motor1)

if __name__ == '__main__':
    try:
        gear = int(sys.argv[1])
        if(gear == 0) : # Pour arrêter le moteur
            m1.stop()
        elif(gear == 1) : # Pour avancer
            speed = 100
            m1.avancer(30)
        elif(gear == 2) : # Pour reculer
            m1.reculer(30)
        else :
            print("0 pour NEUTRE")
            print("1 pour AVANCER")
            print("2 pour RECULER")

    except KeyboardInterrupt:
        print("Programme interrompu.")
    finally :
        m1.destroy()
