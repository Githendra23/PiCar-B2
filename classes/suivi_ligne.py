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
    MOST_LEFT = 130
    MID_LEFT = 110
    MID_RIGHT = 70
    MOST_RIGHT = 50
    try:
        speed = 35
        reverse_speed = 15

        moteur = Moteur.Moteur()
        moteur.drive(speed)
        direction = Direction.Direction()
        capteur_ligne = CapteurSuiviLigne.CapteurSuiviLigne()
        previous_state = (1,1,1)

        
        while True:
            capteur_ligne.printState()
            print("")

            moteur.drive(speed)
            etat = capteur_ligne.getState()

            if(etat == (0,0,0)) : # Pas de ligne noire
                if(previous_state == (1,1,1)) :
                    time.sleep(0.75)
                else :
                    moteur.reverse(reverse_speed)
                    # time.sleep(0.2)
                

            elif(etat == (1,0,0)) : # Braquer à gauche
                moteur.stop()
                direction.turn(MOST_RIGHT)
                moteur.reverse(reverse_speed)
                time.sleep(0.5)
                direction.reset()
                

            elif(etat == (0,0,1)) : # Braquer à droite
                direction.turn(MOST_LEFT)
                moteur.reverse(reverse_speed)
                time.sleep(0.5)
                direction.reset()

            elif(etat == (0,1,1)) :
                angle = MID_RIGHT
                direction.turn(angle) # Tourner à droite de 20°
                print(f"On tourne à droite de {abs(direction.ANGLE_CENTER-angle)}°.")
                time.sleep(0.2)
                direction.reset()

            elif(etat == (1,1,1)) : # Ligne noire => aller tout droit
                moteur.drive(speed)

            elif(etat == (1,1,0)) :
                angle = MID_LEFT
                direction.turn(angle) # Tourner à gauche de 20°
                print(f"On tourne à gauche de {abs(direction.ANGLE_CENTER-angle)}°.")
                time.sleep(0.2)
                direction.reset()

            

            time.sleep(0.05)
            previous_state = etat


    except KeyboardInterrupt:
        print("Fin du programme via le clavier.")
        direction.reset()
        moteur.stop()