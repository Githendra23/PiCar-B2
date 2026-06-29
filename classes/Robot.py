import threading
import time

import Batterie
import Buzzer
import CapteurSuiviLigne
import Direction
import FeuxAvant
import FeuxArriere
import LEDDroitBas
import LEDGaucheBas
import Moteur
import Tourelle



class Robot :
    def __init__(self):
        self.batterie = Batterie.Batterie()
        self.buzzer = Buzzer.Buzzer()
        self.capteurSuiviLigne = CapteurSuiviLigne.CapteurSuiviLigne()
        self.direction = Direction.Direction()
        
        self.feuxAvant = FeuxAvant.FeuxAvant()
        self.feuxArriere = FeuxArriere.setLed(14, 255)
        
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
        thread = threading.Thread(target=self.feuxArriere.blinkAlert)
        thread.start()


    def suiviLigne(self) :
        speed = 35
        reverse_speed = 15
        MOST_LEFT = 130
        MID_LEFT = 110
        MID_RIGHT = 70
        MOST_RIGHT = 50

        self.stopEngine()
        previous_state = (1,1,1)

        # On définit une fonction ici pour le threading.
        # Elle ne servira pas ailleurs.
        def blink() :
            for i in range (4) :
                self.feuxArriere.blinkAlert()
        
        while True:
            self.capteurSuiviLigne.printState()
            print("")

            distanceObstacle = self.tourelle.getDistance()
            print(f"Distance obstacle : {distanceObstacle}mm")
            if(distanceObstacle <= 150) :
                
                if(self.moteur.current_speed != 0) :
                    thread = threading.Thread(target=blink)
                    thread.start()
                    self.stopEngine()

                else :
                    # robot.feuxAvant.warning()
                    self.feuxArriere.sequentialWarning()

                continue
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

    # distanceObstacle en millimètres
    def analyseObstacle(self, distanceObstacle) :
        matriceObstacles = self.tourelle.getMatrixObstacles()

        for i in range(0,180,1) :
            if(matriceObstacles[i] <= distanceObstacle) :
                print(f"Angle {i}° : obstacle")
            else :
                print(f"Angle {i}° : libre")
                continue
    

if __name__ == '__main__':
    robot = Robot()
    print(f"Niveau de batterie : {robot.getBatteryPercentage()}")
    
    try:
        robot.suiviLigne()
        
    except KeyboardInterrupt:
        print("Fin du programme via le clavier.")
    finally :
        robot.direction.reset()
        robot.feuxAvant.off()
        robot.resetTourelle()
        robot.stopEngine()