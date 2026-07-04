import os
import sys

RACINE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(RACINE, "fonctions"))
sys.path.append(os.path.join(RACINE, "classes"))

from FluxVideo import FluxVideo
from Moteur import Moteur
from Direction import Direction
from Tourelle import Tourelle
from FeuxArriere import FeuxArriere

# ==========================================================================
# PARAMETRES DE PILOTAGE (a ajuster au test)
# ==========================================================================
ZONE_MORTE = 40         # marge d'erreur (px) : en dessous -> robot considere centre
GAIN_POSITION = 0.15    # correction basee sur l'ecart lateral
GAIN_ANGLE = 0.40       # correction basee sur l'orientation de la ligne (anticipe les virages)
SENS_SERVO = 1          # 1 ou -1 : a inverser si le robot braque du mauvais cote
VITESSE = 30            # vitesse d'avance

# Active/desactive le flux video web (met False pour alleger le CPU)
STREAMING = False


def calculer_angle_servo(direction, erreur_position, angle_ligne=None):
    """
    Calcule l'angle de braquage a partir des infos de la vision.
      - erreur_position : ecart lateral de la ligne / centre
      - angle_ligne     : orientation de la ligne (facultatif, anticipe les virages)
    """
    centre = direction.getAngleCenter()

    # Dans la zone morte et ligne droite -> tout droit
    if abs(erreur_position) < ZONE_MORTE and (angle_ligne is None or abs(angle_ligne) < 5):
        return centre

    # Correction combinee position (+ angle si disponible)
    correction = erreur_position * GAIN_POSITION
    if angle_ligne is not None:
        correction += angle_ligne * GAIN_ANGLE

    angle = centre - SENS_SERVO * correction
    # On borne dans la plage autorisee du servo
    return int(max(direction.getAngleMin(), min(direction.getAngleMax(), angle)))


def main():
    # --- Vision ---
    camera = FluxVideo(streaming=STREAMING)

    # --- Actionneurs ---
    moteur = Moteur()
    direction = Direction()
    tourelle = Tourelle()
    ledArriere = FeuxArriere()

    # Init
    ledArriere.set_led_brightness(0)
    ledArriere.set_all_led_rgb([0, 0, 0])
    tourelle.reset()
    tourelle.turn_y_axis(50)   # oriente la camera vers le sol

    ligne_deja_detectee = False

    try:
        while True:
            infos = camera.analyser()

            # 1) PRIORITE : ruban bleu -> arret definitif
            if infos["bleu"]:
                moteur.stop()
                direction.reset()
                print("Ruban bleu detecte -> arret de la sequence")
                break

            # 2) Ligne detectee (mode complet OU degrade)
            if infos["ligne_detectee"]:
                ligne_deja_detectee = True
                angle_servo = calculer_angle_servo(
                    direction,
                    infos["erreur_position"],
                    infos["angle"]      # None en mode degrade -> position seule
                )
                direction.turn(angle_servo)
                moteur.drive(VITESSE)

            # 3) Ligne perdue
            else:
                if ligne_deja_detectee:
                    # On a deja vu la ligne : manoeuvre de recherche (recul droit)
                    direction.turn(direction.getAngleCenter())
                    moteur.reverse(VITESSE * 0.3)
                    print("Ligne perdue -> recul de recherche")
                else:
                    # Jamais vu la ligne encore : on attend
                    moteur.stop()

    except KeyboardInterrupt:
        print("Arret manuel")
    finally:
        moteur.destroy()
        direction.reset()
        camera.stop()


if __name__ == "__main__":
    main()