import os
import sys
import time

RACINE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(RACINE, "fonctions"))
from FluxVideo import FluxVideo

sys.path.append(os.path.join(RACINE, "classes"))
from Moteur import Moteur
from Direction import Direction
from Tourelle import Tourelle
from FeuxArriere import FeuxArriere
from FeuxAvant import FeuxAvant

ZONE_MORTE = 40         # marge d'erreur (px) : en dessous -> robot considere centre
GAIN_POSITION = 0.15    # correction basee sur l'ecart lateral
GAIN_ANGLE = 0.40       # correction basee sur l'orientation de la ligne (anticipe les virages)
SENS_SERVO = 1          # 1 ou -1 : a inverser si le robot braque du mauvais côté
VITESSE = 30            # vitesse d'avance

# Seuil (en degres de servo) au-dela duquel on considere que le robot "tourne"
SEUIL_CLIGNOTANT = 15

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


def gerer_clignotants(feuxAvant, direction, angle_servo, maintenant):
    """
    Allume le clignotant selon le sens de braquage :
      - angle > centre + seuil  -> le robot tourne d'un cote  -> clignotant
      - angle < centre - seuil  -> le robot tourne de l'autre -> clignotant
      - proche du centre        -> aucun clignotant (on eteint)

    'maintenant' (ms) est calcule une seule fois dans le main et passe ici,
    pour que le clignotement soit non-bloquant.
    """
    centre = direction.getAngleCenter()
    ecart = angle_servo - centre

    if ecart > SEUIL_CLIGNOTANT:
        # Le robot braque d'un cote : clignotant droit
        feuxAvant.blinker_right(maintenant)
        feuxAvant.left_off()
    elif ecart < -SEUIL_CLIGNOTANT:
        # Le robot braque de l'autre cote : clignotant gauche
        feuxAvant.blinker_left(maintenant)
        feuxAvant.right_off()
    else:
        # Tout droit : pas de clignotant
        feuxAvant.left_off()
        feuxAvant.right_off()


def main():
    camera = FluxVideo(streaming=STREAMING)

    moteur = Moteur()
    direction = Direction()
    tourelle = Tourelle()
    ledArriere = FeuxArriere()
    feuxAvant = FeuxAvant()

    ledArriere.set_led_brightness(0)
    ledArriere.set_all_led_rgb([0, 0, 0])
    feuxAvant.off()
    tourelle.reset()
    tourelle.turn_y_axis(50)

    ligne_deja_detectee = False

    try:
        while True:
            # non-bloquants (clignotants). Chaque effet garde son propre repere.
            maintenant = time.time() * 1000

            infos = camera.analyser()

            # 1) PRIORITE : ruban bleu -> arret definitif
            if infos["bleu"]:
                moteur.stop()
                direction.reset()
                feuxAvant.off()
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

                # Clignotants selon le sens du braquage
                gerer_clignotants(feuxAvant, direction, angle_servo, maintenant)

            # 3) Ligne perdue
            else:
                if ligne_deja_detectee:
                    # On a deja vu la ligne : manoeuvre de recherche (recul droit)
                    direction.turn(direction.getAngleCenter())
                    moteur.reverse(VITESSE * 0.3)
                    feuxAvant.warnings(maintenant)
                    print("Ligne perdue -> recul de recherche")
                else:
                    # Jamais vu la ligne encore : on attend
                    moteur.stop()
                    feuxAvant.off()

    except KeyboardInterrupt:
        print("Arret manuel")
    finally:
        tourelle.turn_y_axis(0)
        moteur.reset()
        moteur.destroy()
        direction.reset()
        feuxAvant.off()
        camera.stop()

if __name__ == "__main__":
    main()