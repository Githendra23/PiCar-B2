import CapteurSuiviLigne
import Direction
import Moteur

import time

MOST_LEFT = 130
MID_LEFT = 110
MID_RIGHT = 70
MOST_RIGHT = 50


def effectuer_x_cm(distance) :
    if(distance < 0) :
        return 0

    speed = 25
    DIAMETRE_ROUES = 20

    return 0


if __name__ == '__main__':
    try:
        speed = 15

        moteur = Moteur.Moteur()
        moteur.avancer(speed)
        direction = Direction.Direction()
        capteur_ligne = CapteurSuiviLigne.CapteurSuiviLigne()

        
        while True:
            capteur_ligne.printState()
            print("")

            etat = capteur_ligne.getState()
            if(etat == (0,0,0)) : # Pas de ligne noire
                time.sleep(0.5)
                etat = capteur_ligne.getState()
                if(etat == (0,0,0)) :
                    moteur.reculer(speed)
                    moteur.avancer(10)

            elif(etat == (0,0,1)) :
                moteur.reculer(10)
                time.sleep(0.5)
                direction.turn(MOST_LEFT)
                moteur.avancer(10)
                time.sleep(0.5)

            elif(etat == (0,1,1)) :
                angle = MID_RIGHT
                direction.turn(angle) # Tourner à droite de 20°
                print(f"On tourne à droite de {abs(direction.ANGLE_CENTER-angle)}°.")
                time.sleep(0.2)
                direction.reset()

            elif(etat == (1,1,1)) : # Ligne noire => aller tout droit
                moteur.avancer(speed)

            elif(etat == (1,1,0)) :
                angle = MID_LEFT
                direction.turn(angle) # Tourner à droite de 20°
                print(f"On tourne à gauche de {abs(direction.ANGLE_CENTER-angle)}°.")
                time.sleep(0.2)
                direction.reset()

            elif(etat == (1,0,0)) :
                moteur.reculer(10)
                time.sleep(0.5)
                direction.turn(MOST_RIGHT)
                moteur.avancer(15)
                time.sleep(0.5)
                direction.reset()

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Fin du programme via le clavier.")
        direction.reset()
        moteur.stop()