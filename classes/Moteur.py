import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import motor

import sys

# motor_EN_A: Pin7  |  motor_EN_B: Pin11
# motor_A:  Pin8,Pin10    |  motor_B: Pin13,Pin12

VMIN = 0
VMAX = 100

def map(x,in_min,in_max,out_min,out_max):
  return (x - in_min)/(in_max - in_min) *(out_max - out_min) +out_min

# Pour bien garder la vitesse entre 0 et 100
def check_speed(vitesse) :
    if(vitesse > VMAX) :
        vitesse = VMAX
    elif(vitesse < VMIN) :
        vitesse = VMIN
    return vitesse

class Moteur:
    def __init__(self):
        MOTOR_M1_IN1 =  15      #Define the positive pole of M1
        MOTOR_M1_IN2 =  14      #Define the negative pole of M1
        pwn_A = 0
        pwm_B = 0

        i2c = busio.I2C(SCL, SDA)
        # Create a simple PCA9685 class instance.
        #  pwm_motor.channels[7].duty_cycle = 0xFFFF
        self.pwm_motor = PCA9685(i2c, address=0x5f) #default 0x40
        self.pwm_motor.frequency = 50

        self.moteur = motor.DCMotor(self.pwm_motor.channels[MOTOR_M1_IN1],self.pwm_motor.channels[MOTOR_M1_IN2])
        self.moteur.decay_mode = (motor.SLOW_DECAY)

        self.current_speed = 0
        self.gear = 'N'
    
    # Pour avancer
    def drive(self, speed):
        speed = check_speed(speed)
        # print(f"Le moteur avance ! Vitesse : {speed}")

        diff = abs(self.current_speed - speed)
        if(diff >= 30) :
            # print("Progressif")
            self.progress_start(speed,1)
        else :
            self.moteur.throttle = map(speed, 0, 100, 0, 1.0)
        self.current_speed = speed
        self.gear = 'D'


    # Pour reculer
    def reverse(self, speed):
        speed = check_speed(speed)
        # print(f"Le moteur recule ! Vitesse : {speed}")

        diff = abs(self.current_speed - speed)
        if(diff >= 30) :
            # print("Progressif")
            self.progress_start(speed,-1)
        else :
            self.moteur.throttle = -map(speed, 0, 100, 0, 1.0)
        self.current_speed = speed
        self.gear = 'R'

    # Pour un démarrage progressif afin de ne pas abîmer la transmission
    def progress_start(self, speed, direction) :
        acceleration_delay = 0.05
        speed = check_speed(speed)
        
        for i in range(speed) :
            if(direction < 0) :
              direction = -1
            else :
              direction = 1

            
            self.moteur.throttle = direction*map(i,0,100,0,1.0)
            self.current_speed = i
            time.sleep(acceleration_delay)
  
    # Arrêter le moteur
    def stop(self):
        # print("Le moteur est à l'arrêt !")
        self.moteur.throttle = 0
        self.current_speed = 0
        self.gear = 'N'

    # Contrôle de traction, si les roues motrices patinent
    def TC(self, speed) :
        self.stop()
        time.sleep(1/20)
        self.drive(speed)
        time.sleep(1/20)

    # Déconnecter le moteur
    def destroy(self):
        # print("Destruction du moteur.")
        self.stop()
        self.pwm_motor.deinit()


# Pour faire un test
if __name__ == '__main__':
    # Création d'une instance du moteur
    unMoteur = Moteur()
    try:
        gear = int(sys.argv[1])

        if gear == 0: # Pour arrêter le moteur
            unMoteur.stop()

        elif gear == 1: # Pour avancer
            speed = 50
            print(f"Current : {unMoteur.current_speed}")

            while True :
                unMoteur.drive(speed)
                time.sleep(0.1)

        elif gear == 2: # Pour reculer
            speed = 30

            while True :
                unMoteur.reverse(speed)
                time.sleep(2)
            
        else : # Si l'utilisateur ne saisit pas une bonne entrée
            print("0 pour NEUTRE")
            print("1 pour AVANCER")
            print("2 pour RECULER")

    except KeyboardInterrupt:
        print("Programme interrompu.")
        
    finally :
        unMoteur.destroy()
