import threading
import time

import Batterie
import Buzzer
import CapteurSuiviLigne
import Direction
import self_components.FeuxAvant as FeuxAvant
import self_components.FeuxArriere as FeuxArriere
import self_components.LEDDroitBas as LEDDroitBas
import self_components.LEDGaucheBas as LEDGaucheBas
import Moteur
import Tourelle



class Robot :
    def __init__(self):
        self.batterie = Batterie.Batterie()
        self.buzzer = Buzzer.Buzzer()
        self.capteurSuiviLigne = CapteurSuiviLigne.CapteurSuiviLigne()
        self.direction = Direction.Direction()
        
        self.feuxAvant = FeuxAvant.FeuxAvant()
        self.feuxArriere = FeuxArriere.FeuxArriere(14)
        
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
        speed = 25
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
                time.sleep(0.5)
                self.direction.turn(MOST_LEFT)
                self.drive(15)
                time.sleep(0.5)
                self.direction.reset()

            elif(etat == (0,0,1)) : # Virage fort à droite
                self.stopEngine()
                self.direction.turn(MOST_LEFT)
                self.reverse(15)
                time.sleep(0.5)
                self.direction.turn(MOST_RIGHT)
                self.drive(15)
                time.sleep(0.5)
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

            time.sleep(0.01)
            previous_state = etat

    def blackLineDetected(self) :
        etat = self.capteurSuiviLigne.getState()
        if(etat != (0,0,0)) :
            return True
        return False

    def getLargestFreeBand(self, binaryMatrix, step):
        best_start = -1
        best_end = -1
        best_len = 0

        current_start = None

        for i, value in enumerate(binaryMatrix):
            if value == 0:
                if current_start is None:
                    current_start = i
            else:
                if current_start is not None:
                    current_len = i - current_start
                    if current_len > best_len:
                        best_len = current_len
                        best_start = current_start
                        best_end = i - 1
                    current_start = None

        # Cas où la plus longue portion de 0 va jusqu'à la fin du vecteur
        if current_start is not None:
            current_len = len(binaryMatrix) - current_start
            if current_len > best_len:
                best_start = current_start
                best_end = len(binaryMatrix) - 1

        return best_start*step, best_end*step

    # distanceObstacle en millimètres
    def detectionObstacle(self) :
        MOST_LEFT = 140
        MOST_RIGHT = 40
        distanceAlerte = 150
        speed = 15
        self.tourelle.reset() # On centre la tourelle
        step = 18

        while True :
            self.stopEngine()

            matriceObstacles = self.tourelle.getMatrixObstacles(step,printAngle=False)
            # print(matriceObstacles)
            matriceBinaire = Tourelle.toBinary(matriceObstacles, distanceAlerte)


            minAngle, maxAngle = self.getLargestFreeBand(matriceBinaire, step)
            if(minAngle == maxAngle) :
                print("Pépin !")
                minAngle = 0
                maxAngle = 180
            print(f"Min : {minAngle}° et Max : {maxAngle}")

            angleBraquage = (minAngle + maxAngle)/2
            print(f"Angle braquage : {angleBraquage}°")
            self.direction.turn(angleBraquage)

            forwardTime = 0
            self.tourelle.turnXAxis(angleBraquage)
            while(not(self.blackLineDetected()) and (forwardTime < 2) and (self.tourelle.getDistance() >= 150)) :
                self.drive(speed)
                forwardTime = forwardTime + 0.1
                time.sleep(0.1)

            self.stopEngine()
            self.tourelle.reset()
            
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
        robot.detectionObstacle()

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