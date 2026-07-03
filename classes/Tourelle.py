import time

import CapteurUltrason
import ServoController

ANGLE_MAX = 180
ANGLE_MIN = 0

############################
# AJOUTER LA LOGIQUE DU CAPTEUR ULTRASON
# AJOUTER LES TRUCS POUR LA CAMÉRA
############################

class Tourelle:
    def __init__(self):
        self.CHANNEL_X_AXIS = 1 # horizontal
        self.CHANNEL_Y_AXIS = 2 # vertical
        
        self.controller = ServoController.ServoController()
        self.controller.add_servo(self.CHANNEL_X_AXIS)
        self.controller.add_servo(self.CHANNEL_Y_AXIS)
        
        self.capteurUltrason = CapteurUltrason.CapteurUltrason()

    def turnXAxis(self, angle):
        if (angle >= ANGLE_MIN and angle <= ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL_X_AXIS, angle)
        else:
            ValueError("Tourelle rotation X - Angle hors de portée")

    def turnYAxis(self, angle):
        if (angle >= ANGLE_MIN and angle <= ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL_Y_AXIS, angle)
        else:
            ValueError("Tourelle rotation Y - Angle hors de portée")

    def obstacleNearby(self, matrix, distanceAlerte) :
        for i in range(len(matrix)) :
            if(matrix[i] <= distanceAlerte) :
                return True
            
        return False

    def getMatrixObstacles(self) :
        matrice = []
        # anglesDetection = [0,45,90,135,180]
        self.reset()

        self.turnXAxis(0)
        time.sleep(1)
        for angle in range(0,180) :
            self.turnXAxis(angle)
            print(f"Angle : {angle}°")
            time.sleep(0.01)

            matrice.append(self.capteurUltrason.distance())
        
        return matrice

    def getDistance(self) :
        return self.capteurUltrason.distance()

    def clearAround(self, matrix, distanceAlerte) :
        for i in range(len(matrix)) :
            if(matrix[i] <= distanceAlerte) :
                return False
        return True


    def printAngles(self) :
        print(f"Angle X : ")
        print(f"Angle Y : ")

    def getAngleMax(self):
        return self.ANGLE_MAX

    def getAngleMin(self):
        return self.ANGLE_MIN

    def reset(self):
        self.turnXAxis(90)
        self.turnYAxis(90)


if __name__ == "__main__" :
    tourelle = Tourelle()

    try :
        # x_angle = int(input("Entrez l'angle sur l'axe X : "))
        # y_angle = int(input("Entrez l'angle sur l'axe Y : "))

        # tourelle.turnXAxis(x_angle)
        # tourelle.turnYAxis(y_angle)
        # # tourelle.print_angle()
        
        tourelle.reset()
        time.sleep(1)
            
    except KeyboardInterrupt :
        print("Fin du programme.")
        tourelle.reset()
