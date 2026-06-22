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
        # self.feuxArriere = FeuxArriere.FeuxArriere()
        
        self.ledGaucheBas = LEDGaucheBas.LEDGaucheBas()
        self.ledDroitBas = LEDDroitBas.LEDDroitBas()
        
        self.moteur = Moteur.Moteur()
        self.tourelle = Tourelle.Tourelle()

    
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
        

    def suiviLigne(self) :
        speed = 35
        reverse_speed = 15
        MOST_LEFT = 130
        MID_LEFT = 110
        MID_RIGHT = 70
        MOST_RIGHT = 50

        robot.drive(speed)
        previous_state = (1,1,1)

        
        while True:
            robot.capteurSuiviLigne.printState()
            print("")

            robot.drive(speed)
            etat = robot.capteurSuiviLigne.getState()

            if(etat == (0,0,0)) : # Pas de ligne noire
                if(previous_state == (1,1,1)) :
                    time.sleep(0.75)
                else :
                    robot.reverse(reverse_speed)
                    # time.sleep(0.2)
                

            elif(etat == (1,0,0)) : # Braquer à gauche
                robot.stopEngine()
                robot.direction.turn(MOST_RIGHT)
                robot.reverse(15)
                time.sleep(0.25)
                robot.direction.turn(MOST_LEFT)
                robot.drive(15)
                time.sleep(0.25)
                robot.direction.reset()
                

            elif(etat == (0,0,1)) : # Braquer à droite
                robot.stopEngine()
                robot.direction.turn(MOST_LEFT)
                robot.reverse(15)
                time.sleep(0.25)
                robot.direction.turn(MOST_RIGHT)
                robot.drive(15)
                time.sleep(0.25)
                robot.direction.reset()

            elif(etat == (0,1,1)) :
                angle = MID_RIGHT
                robot.direction.turn(angle) # Tourner à droite de 20°
                print(f"On tourne à droite de {abs(robot.direction.ANGLE_CENTER-angle)}°.")
                time.sleep(0.2)
                robot.direction.reset()

            elif(etat == (1,1,1)) : # Ligne noire => aller tout droit
                robot.drive(speed)

            elif(etat == (1,1,0)) :
                angle = MID_LEFT
                robot.direction.turn(angle) # Tourner à gauche de 20°
                print(f"On tourne à gauche de {abs(robot.direction.ANGLE_CENTER-angle)}°.")
                time.sleep(0.2)
                robot.direction.reset()

            time.sleep(0.05)
            previous_state = etat



if __name__ == '__main__':
    robot = Robot()
    print(f"Niveau de batterie : {robot.getBatteryPercentage()}")
    
    try:
        robot.suiviLigne()
        # while True :
        #     robot.feuxAvant.warning()

    except KeyboardInterrupt:
        print("Fin du programme via le clavier.")
    finally :
        robot.direction.reset()
        robot.feuxAvant.off()
        robot.resetTourelle()
        robot.stopEngine()