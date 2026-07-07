import time

import self_components.CapteurUltrason as CapteurUltrason
from ServoController import ServoController

ANGLE_MAX = 180
ANGLE_MIN = 0

############################
# AJOUTER LES TRUCS POUR LA CAMÉRA
############################

class Tourelle:
    def __init__(self):
        self.CHANNEL_X_AXIS = 1 # horizontal
        self.CHANNEL_Y_AXIS = 2 # vertical
        
        self.controller = ServoController()
        self.controller.add_servo(self.CHANNEL_X_AXIS)
        self.controller.add_servo(self.CHANNEL_Y_AXIS)
        
        self.capteurUltrason = CapteurUltrason.CapteurUltrason()

        self.angle_x_actuel = None
        self.angle_y_actuel = None

    def turnXAxis(self, angle):
        if (angle >= ANGLE_MIN and angle <= ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL_X_AXIS, angle)
            self.controller.set_angle(self.CHANNEL_X_AXIS, angle)
            self.angle_x_actuel = angle
        else:
            ValueError("Tourelle rotation X - Angle hors de portée")

    def turnYAxis(self, angle):
        if (angle >= ANGLE_MIN and angle <= ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL_Y_AXIS, angle)
            self.angle_y_actuel = angle
        else:
            ValueError("Tourelle rotation Y - Angle hors de portée")
    
    def release_x_axis(self):
        """
        Coupe le signal PMW du servo horizontal.
        """

        self.controller.release_servo(self.CHANNEL_X_AXIS)

    # Renvoie True si un obstacle se trouve près de la tourelle, False sinon
    def obstacleNearby(self, matrix, distanceAlerte) :
        for i in range(len(matrix)) :
            if(matrix[i] <= distanceAlerte) :
                return True
        return False

    # Renvoie la matrice des obstacles autour de la tourelle
    def getMatrixObstacles(self, printAngle : bool) :
        matrice = []
        # anglesDetection = [0,45,90,135,180]
        self.reset()

        self.turnXAxis(0)
        time.sleep(1)
        for angle in range(0,180) :
            self.turnXAxis(angle)
            if(printAngle) :
                # print(f"Angle : {angle}°")
                pass
            time.sleep(0.05)

            matrice.append(self.capteurUltrason.distance())
        self.reset()
        return matrice
    
    # Renvoie l'index matriciel de l'obstacle le plus proche
    def getNearestObstacleIndex(self, matrix) :
        minimum = 0
        for i in range(len(matrix)) :
            if(matrix[i] < minimum) :
                minimum = i
        return i

    # Affiche les obstacles avec des 0 (si pas d'obstacle) et des 1 (si obstacle)
    def printBinaryMatrixObstacles(self, matrix, distanceAlerte) :
        for i in range(0,len(matrix),1) :
            if(matrix[i] <= distanceAlerte) :
                print("1",end="")
            else :
                print("0",end="")
        print("")

    def getDistance(self) :
        return self.capteurUltrason.distance()

    # Renvoie True s'il n'y a pas d'obstacles autour de la tourelle
    def clearAround(self, matrix, distanceAlerte) :
        for i in range(len(matrix)) :
            if(matrix[i] <= distanceAlerte) :
                return False
        return True


    def printAngles(self) :
        print(f"Angle X : ")
        print(f"Angle Y : ")

    # Recentre la tourelle
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
