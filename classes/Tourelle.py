import time

import self_components.CapteurUltrason as CapteurUltrason
from ServoController import ServoController

ANGLE_MAX = 180
ANGLE_MIN = 0

############################
# AJOUTER LES TRUCS POUR LA CAMÉRA
############################


def getNearestObstacleAngle(matrix) :
    minimum = matrix[0]
    angle = 0
    for i in range(len(matrix)) :
        if(matrix[i] == -1) :
            continue
        if(matrix[i] < minimum) :
            angle = i
    return angle

# Affiche les obstacles avec des 0 (si pas d'obstacle) et des 1 (si obstacle)
def printBinaryMatrixObstacles(matriceBinaire) :
    for i in range(len(matriceBinaire)) :
            print(f"{matriceBinaire[i]}",end="")
    print("")

def toBinary(matrix, distanceAlerte) :
    matriceBinaire = []
    for i in range(180) :
        if(matrix[i] == -1) :
            continue
        
        if(matrix[i] <= distanceAlerte) :
            matriceBinaire.append(1)
        else :
            matriceBinaire.append(0)
    # print("Matrice binaire : ",matriceBinaire)
    return matriceBinaire

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
            self.angle_x_actuel = angle
        else:
            ValueError("Tourelle rotation X - Angle hors de portée")

    def turnYAxis(self, angle):
        if (angle >= ANGLE_MIN and angle <= ANGLE_MAX):
            self.controller.set_angle(self.CHANNEL_Y_AXIS, angle)
            self.angle_y_actuel = angle
        else:
            ValueError("Tourelle rotation Y - Angle hors de portée")
    
    def printAngles(self):
        """
        Affiche les angles actuels de la tourelle.
        """
        print(f"Angle X : {self.angle_x_actuel}°")
        print(f"Angle Y : {self.angle_y_actuel}°")

    def release_x_axis(self):
        """
        Coupe le signal PMW du servo horizontal.
        """

        self.controller.release_servo(self.CHANNEL_X_AXIS)

    # Renvoie la matrice des obstacles autour de la tourelle
    def getMatrixObstacles(self, step, yAngle ,timeSurround, printAngle : bool) :
        matrice = [-1]*180
        # anglesDetection = [0,45,90,135,180]
        self.reset()

        self.turnXAxis(0)
        self.turnYAxis(yAngle)
        time.sleep(1)
        
        for angle in range(0, 180, step) :
            self.turnXAxis(angle)
            matrice[angle] = self.capteurUltrason.distance()
            if(printAngle) :
                print(f"Angle : {angle}°")
            time.sleep(timeSurround)

        self.reset()
        return matrice

    def getDistance(self) :
        return self.capteurUltrason.distance()

    # Recentre la tourelle
    def reset(self):
        self.turnXAxis(90)
        self.turnYAxis(90)


if __name__ == "__main__" :
    tourelle = Tourelle()

    try :
        x_angle = int(input("Entrez l'angle sur l'axe X : "))
        y_angle = int(input("Entrez l'angle sur l'axe Y : "))

        tourelle.turnXAxis(x_angle)
        tourelle.turnYAxis(y_angle)
        # tourelle.print_angle()
        
        # tourelle.reset()
        time.sleep(1)
            
    except KeyboardInterrupt :
        print("Fin du programme.")
        tourelle.reset()
