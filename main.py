import os
import sys
import time

import classes.self_components.FeuxArriere as FeuxArriere
import classes.self_components.FeuxAvant as FeuxAvant

RACINE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(RACINE, "fonctions"))
from FluxVideo import FluxVideo

sys.path.append(os.path.join(RACINE, "classes"))
from Moteur import Moteur
from Direction import Direction
from Tourelle import Tourelle



# ==========================================================================
# PARAMETRES DE PILOTAGE (a ajuster au test)
# ==========================================================================
ZONE_MORTE = 40         # marge d'erreur (px) : en dessous -> robot considere centre
GAIN_POSITION = 0.15    # correction basee sur l'ecart lateral
GAIN_ANGLE = 0.40       # correction basee sur l'orientation de la ligne (anticipe les virages)
SENS_SERVO = 1          # 1 ou -1 : a inverser si le robot braque du mauvais côté
VITESSE = 35            # vitesse d'avance
SEUIL_CLIGNOTANT = 15   # seuil (deg servo) au-dela duquel on allume un clignotant

STREAMING = True


# ==========================================================================
# FONCTIONS UTILITAIRES DE PILOTAGE
# ==========================================================================
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
    return int(max(direction.getAngleMin(), min(direction.getAngleMax(), angle)))


def gerer_clignotants(feuxAvant, direction, angle_servo, maintenant):
    """Allume le clignotant selon le sens de braquage (non-bloquant)."""
    centre = direction.getAngleCenter()
    ecart = angle_servo - centre

    if ecart > SEUIL_CLIGNOTANT:
        feuxAvant.blinker_right(maintenant)
        feuxAvant.left_off()
    elif ecart < -SEUIL_CLIGNOTANT:
        feuxAvant.blinker_left(maintenant)
        feuxAvant.right_off()
    else:
        feuxAvant.left_off()
        feuxAvant.right_off()

def suivre_ligne_rouge(camera, moteur, direction, feuxAvant=None):
    """
    Suit la ligne rouge : centre le robot, avance, gere les virages.
    S'arrete quand le ruban bleu est detecte.

    Retourne une chaine indiquant POURQUOI la mission s'est terminee :
      - "bleu"       : ruban bleu atteint (fin normale)
      - "interrompu" : arret manuel (Ctrl-C)

    Le main peut utiliser cette valeur de retour pour enchainer la mission suivante.
    """
    ligne_deja_detectee = False

    while True:
        # Horloge lue une seule fois par tour (pour les effets non-bloquants)
        maintenant = time.time() * 1000

        infos = camera.analyser()

        # 1) PRIORITE : ruban bleu -> fin de la mission
        if infos["bleu"]:
            moteur.stop()
            direction.reset()
            if feuxAvant:
                feuxAvant.off()
            print("Ruban bleu detecte -> fin du suivi de ligne")
            return "bleu"

        # 2) Ligne detectee -> centrage + suivi
        if infos["ligne_detectee"]:
            ligne_deja_detectee = True
            angle_servo = calculer_angle_servo(
                direction,
                infos["erreur_position"],
                infos["angle"]      # None en mode degrade -> position seule
            )
            direction.turn(angle_servo)
            moteur.drive(VITESSE)

            if feuxAvant:
                gerer_clignotants(feuxAvant, direction, angle_servo, maintenant)

        # 3) Ligne perdue
        else:
            if ligne_deja_detectee:
                # Deja vu la ligne : roues droites + recul jusqu'a la retrouver
                direction.turn(direction.getAngleCenter())
                moteur.reverse(VITESSE * 0.5)
                if feuxAvant:
                    feuxAvant.warnings(maintenant)
                print("Ligne perdue -> recul de recherche")
            else:
                # Jamais vu la ligne : on attend
                moteur.stop()
                if feuxAvant:
                    feuxAvant.off()


# ==========================================================================
# MISSION 2, 3, ... (a remplir plus tard)
# ==========================================================================
def resoudre_labyrinthe(camera, moteur, direction, feuxAvant=None):
    """Navigation dans le labyrinthe via detection de fleches. (a implementer)"""
    pass


def detecter_fleches(camera, moteur, direction, feuxAvant=None):
    """Detection de fleches directionnelles. (a implementer)"""
    pass

def suivi_ligne_noire():
    pass


# ==========================================================================
# ORCHESTRATION : le main initialise le materiel et enchaine les missions
# ==========================================================================
def main():
    # --- Vision ---
    camera = FluxVideo(streaming=STREAMING)

    # --- Actionneurs ---
    moteur = Moteur()
    direction = Direction()
    tourelle = Tourelle()
    ledArriere = FeuxArriere()
    # feuxAvant = FeuxAvant()
    feuxAvant = None

    ledArriere.set_led_brightness(0)
    ledArriere.set_all_led_rgb([0, 0, 0])
    tourelle.turn_y_axis(50)

    try:
        # Mission 1 : suivre la ligne rouge jusqu'au ruban bleu
        resultat = suivre_ligne_rouge(camera, moteur, direction, feuxAvant)

        # Ici, plus tard, on enchaine selon le resultat :
        # if resultat == "bleu":
        #     resoudre_labyrinthe(camera, moteur, direction, feuxAvant)

    except KeyboardInterrupt:
        print("Arret manuel")
    finally:
        tourelle.turn_y_axis(0)
        moteur.destroy()
        direction.reset()
        if feuxAvant:
            feuxAvant.off()
        camera.stop()


if __name__ == "__main__":
    main()