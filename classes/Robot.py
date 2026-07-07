import threading
import time
import sys
import os

import Batterie
import Buzzer
import CapteurSuiviLigne
import Direction
import Moteur
import Tourelle

RACINE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(RACINE, "self_components"))
import FeuxAvant as FeuxAvant
import FeuxArriere as FeuxArriere
import LEDDroitBas as LEDDroitBas
import LEDGaucheBas as LEDGaucheBas


class Robot :
    def __init__(self):
        self.batterie = Batterie.Batterie()
        self.buzzer = Buzzer.Buzzer()
        self.capteurSuiviLigne = CapteurSuiviLigne.CapteurSuiviLigne()
        self.direction = Direction.Direction()
        
        self.feuxAvant = FeuxAvant.FeuxAvant()
        self.feuxArriere = FeuxArriere.FeuxArriere()
        
        self.ledGaucheBas = LEDGaucheBas.LEDGaucheBas()
        self.ledDroitBas = LEDDroitBas.LEDDroitBas()
        
        self.moteur = Moteur.Moteur()
        self.tourelle = Tourelle.Tourelle()

        self.sema_feux_arriere = threading.Semaphore(1)


    def bip(self) :
        self.buzzer.bip()
    
    def getBatteryPercentage(self) :
        return self.batterie.getPercentage()

    def drive(self, speed) :
        self.moteur.drive(speed)

    def reverse(self, speed) :
        self.moteur.reverse(speed)

    def stopEngine(self) :
        self.moteur.stop()

    def resetTourelle(self) :
        self.tourelle.reset()

    def turnTourelleXAxis(self, angle) :
        self.tourelle.turn_x_axis(angle)
    
    def turnTourelleYAxis(self, angle) :
        self.tourelle.turn_y_axis(angle)
        
    def blinkAlert(self) :
        for i in range (4) :
            self.feuxArriere.blinkAlert()

    def warnings(self) :
        self.feuxAvant.warningsOn()
        self.feuxArriere.sequentialWarningsOn()
        time.sleep(0.3)
        self.feuxAvant.off()
        self.feuxArriere.off()
        time.sleep(0.3)

    def pushOnThread(self, functionName) :
        thread = threading.Thread(target=functionName)
        thread.start()

    def suiviLigne(self) :
        speed = 35
        reverse_speed = 15
        MOST_LEFT = 130
        MID_LEFT = 110
        MID_RIGHT = 70
        MOST_RIGHT = 50

        self.stopEngine()
        self.tourelle.reset()
        previous_state = (1,1,1)

        
        while True:
            self.capteurSuiviLigne.printState()
            print("")

            distanceObstacle = self.tourelle.getDistance()
            print(f"Distance obstacle : {distanceObstacle}mm")
            if(distanceObstacle <= 150) : # Si un obstacle est détecté
                
                if(self.moteur.current_speed != 0) : # Si la voiture n'est pas encore arrêtée
                    self.stopEngine()
                    self.blinkAlert()

                else : # Si la voiture s'est arrêtée
                    self.warnings()

                continue # Pour ne pas traiter les cas de détection de ligne en-dessous
            else :
                self.drive(speed)

            etat = self.capteurSuiviLigne.getState()

            if(etat == (0,0,0)) : # Pas de ligne noire
                if(previous_state == (1,1,1)) :
                    time.sleep(0.75)
                else :
                    self.reverse(reverse_speed)
                    # time.sleep(0.2)  

            elif(etat == (1,0,0)) : # Virage fort à gauche
                self.stopEngine()
                self.direction.turn(MOST_RIGHT)
                self.reverse(15)
                time.sleep(0.25)
                self.direction.turn(MOST_LEFT)
                self.drive(15)
                time.sleep(0.25)
                self.direction.reset()

            elif(etat == (0,0,1)) : # Virage fort à droite
                self.stopEngine()
                self.direction.turn(MOST_LEFT)
                self.reverse(15)
                time.sleep(0.25)
                self.direction.turn(MOST_RIGHT)
                self.drive(15)
                time.sleep(0.25)
                self.direction.reset()

            elif(etat == (0,1,1)) :
                angle = MID_RIGHT
                self.direction.turn(angle) # Tourner à droite de 20°
                print(f"On tourne à droite de {abs(self.direction.ANGLE_CENTER-angle)}°.")
                time.sleep(0.2)
                self.direction.reset()

            elif(etat == (1,1,1)) : # Ligne noire => aller tout droit
                self.drive(speed)

            elif(etat == (1,1,0)) :
                angle = MID_LEFT
                self.direction.turn(angle) # Tourner à gauche de 20°
                print(f"On tourne à gauche de {abs(self.direction.ANGLE_CENTER-angle)}°.")
                time.sleep(0.2)
                self.direction.reset()

            time.sleep(0.05)
            previous_state = etat

    def blackLineDetected(self) :
        etat = self.capteurSuiviLigne.getState()
        if(etat != (0,0,0)) :
            return True
        return False

    def getLargestFreeBand(self, matrix, distanceAlerte):
        if self.tourelle.clearAround(matrix, distanceAlerte):
            return 0, 180

        minAngle = 0
        maxAngle = 0
        bestSize = -1

        i = 0
        while i < len(matrix):
            # On saute les zones non libres
            if matrix[i] <= distanceAlerte:
                i += 1
                continue

            # Début d'une zone libre
            start = i

            while i < len(matrix) and matrix[i] > distanceAlerte:
                i += 1

            end = i - 1
            size = end - start

            if size > bestSize:
                minAngle = start
                maxAngle = end
                bestSize = size

        return minAngle, maxAngle

    # distanceObstacle en millimètres
    def analyseObstacle(self) :
        MOST_LEFT = 140
        MOST_RIGHT = 40
        distanceAlerte = 200
        speed = 15
        self.tourelle.reset() # On centre la tourelle

        while True :
            self.stopEngine()

            matriceObstacles = self.tourelle.getMatrixObstacles(printAngle=False)
            self.tourelle.printBinaryMatrixObstacles(matriceObstacles, distanceAlerte)
            # time.sleep(0.5)

            minAngle, maxAngle = self.getLargestFreeBand(matriceObstacles, distanceAlerte)
            if(minAngle == maxAngle) :
                print("Pépin !")
                # return
                minAngle = 0
                maxAngle = 180
            print(f"Min : {minAngle}° et Max : {maxAngle}")

            angleBraquage = (minAngle + maxAngle)/2
            print(f"Angle braquage : {angleBraquage}°")
            self.direction.turn(angleBraquage)

            forwardTime = 0
            self.tourelle.turnXAxis(angleBraquage)
            while(not(self.blackLineDetected()) and (forwardTime < 3) and (self.tourelle.getDistance() >= 150)) :
                self.drive(speed)
                forwardTime = forwardTime + 0.1
                time.sleep(0.1)

            self.stopEngine()
            self.tourelle.reset()

            
            matriceObstacles = self.tourelle.getMatrixObstacles(printAngle=False)
            if(self.tourelle.obstacleNearby(matriceObstacles, 150)) :
            # if(self.tourelle.getDistance() <= 150) : # Si durant le drive on se retrouve face à un obstacle
                self.direction.reset()
                print("Obstacle devant ! On recule !")
                self.moteur.reverse(10)
                self.direction.turn(MOST_LEFT)
                time.sleep(1)
                self.direction.reset()
                continue
            
            self.drive(speed)
            etat = self.capteurSuiviLigne.getState()
            gauche, milieu, droite = etat
            print(f"Bande noire : {gauche},{milieu},{droite}")
            if(self.blackLineDetected()) :
                
                reverse_time = 0.2
                if(etat == (0,0,1)) :
                    self.direction.turn(MOST_LEFT)
                    print(f"GEAR : {self.moteur.gear}")
                
                elif(etat == (0,1,1)) :
                    self.reverse(15)
                    time.sleep(reverse_time)
                    self.direction.turn(MOST_LEFT)
                
                elif(etat == (1,1,1)) :
                    self.stopEngine()
                    self.direction.turn(MOST_RIGHT)
                    self.reverse(10)
                    time.sleep(2)
                    self.direction.reset()
                    self.stopEngine()
                
                elif(etat == (1,1,0)) :
                    self.reverse(15)
                    time.sleep(reverse_time)
                    self.direction.turn(MOST_RIGHT)
                
                elif(etat == (1,0,0)) :
                    self.direction.turn(MOST_RIGHT)
                    print("On avance")

                
                time.sleep(1)

            self.direction.reset()
            print("")


if __name__ == '__main__':
    robot = Robot()
    print(f"Niveau de batterie : {robot.getBatteryPercentage()}")
    
    try:
        robot.suiviLigne()

        # while True :
        #     angleX = int(input("Angle : "))
        #     robot.tourelle.turnXAxis(angleX)
        #     distanceObstacle = robot.tourelle.getDistance()
        #     print(f"Obstacle : {distanceObstacle}mm")
        
    except KeyboardInterrupt:
        print("Fin du programme via le clavier.")
    finally :
        robot.stopEngine()
        robot.direction.reset()
        robot.feuxAvant.off()
        robot.resetTourelle()