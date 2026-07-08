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
from CapteurSuiviLigne import CapteurSuiviLigne

sys.path.append(os.path.join(RACINE, "classes", "self_components"))
from FeuxArriere import FeuxArriere
from FeuxAvant import FeuxAvant


# ==========================================================================
# PARAMETRES DE PILOTAGE (a ajuster au test)
# ==========================================================================
ZONE_MORTE = 40         # marge d'erreur (px) : en dessous -> robot considere centre
GAIN_POSITION = 0.15    # correction basee sur l'ecart lateral
GAIN_ANGLE = 0.40       # correction basee sur l'orientation de la ligne (anticipe les virages)
SENS_SERVO = 1          # 1 ou -1 : a inverser si le robot braque du mauvais côté
VITESSE = 36            # vitesse d'avance
SEUIL_CLIGNOTANT = 15   # seuil (deg servo) au-dela duquel on allume un clignotant

STREAMING = False


# ==========================================================================
# FONCTIONS UTILITAIRES DE PILOTAGE
# ==========================================================================
def calculer_angle_servo(direction, erreur_position, angle_ligne=None):
    """Calcule l'angle de braquage a partir des infos de la vision."""
    centre = direction.getAngleCenter()

    if abs(erreur_position) < ZONE_MORTE and (angle_ligne is None or abs(angle_ligne) < 5):
        return centre

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


# ==========================================================================
# MISSION : SUIVI DE LIGNE ROUGE (camera)
# ==========================================================================
def suivre_ligne_rouge(camera, moteur, direction, feuxAvant=None):
    """
    Suit la ligne rouge : centre le robot, avance, gere les virages.
    S'arrete quand le ruban bleu est detecte. Retourne "bleu" a la fin.
    """
    ligne_deja_detectee = False

    while True:
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
                infos["angle"]
            )
            direction.turn(angle_servo)
            moteur.drive(VITESSE)
            if feuxAvant:
                gerer_clignotants(feuxAvant, direction, angle_servo, maintenant)

        # 3) Ligne perdue
        else:
            if ligne_deja_detectee:
                direction.turn(direction.getAngleCenter())
                moteur.reverse(VITESSE * 0.5)
                if feuxAvant:
                    feuxAvant.warnings(maintenant)
                print("Ligne perdue -> recul de recherche")
            else:
                moteur.stop()
                if feuxAvant:
                    feuxAvant.off()


# ==========================================================================
# MISSION : SUIVI DE LIGNE NOIRE (capteur IR 3 voies)
# ==========================================================================
def suivi_ligne_noire(capteur, moteur, direction):
    """
    Suit une ligne noire avec les 3 capteurs IR (1 = noir, 0 = blanc).
    Gère les lignes discontinues droites en maintenant le cap pendant les coupures.
    """
    # --- Configuration des angles de braquage et constantes ---
    ANGLE_CENTRE = 90
    ANGLE_45_GAUCHE = 100     # Virage doux gauche
    ANGLE_45_DROITE = 80      # Virage doux droite
    ANGLE_FOND_GAUCHE = 140   # Virage serré gauche
    ANGLE_FOND_DROITE = 50    # Virage serré droite
    
    VITESSE = 25
    VITESSE_RECUL = 15
    DELAI_GAP_BLANC = 1.2     # Temps (secondes) maximal autorisé pour franchir l'espace blanc
    
    dernier_braquage = ANGLE_CENTRE
    dernier_type = "droit"     # 'droit' | '45' | 'fond'
    temps_perte = None

    while True:
        gauche, milieu, droite = capteur.getState()

        print(f"gauche : ${gauche}, milieu : ${milieu}, droite : ${droite}")

        ligne_visible = (gauche or milieu or droite)

        if ligne_visible:
            # Réinitialisation immédiate dès qu'un segment noir réapparaît
            temps_perte = None

            # --- Tout droit ---
            if (milieu and not gauche and not droite) or (gauche and milieu and droite) or (droite and gauche and not milieu):
                direction.turn(ANGLE_CENTRE)
                moteur.drive(VITESSE)
                dernier_braquage = ANGLE_CENTRE
                dernier_type = "droit"

            # --- Virage doux (milieu + un cote) ---
            elif milieu and gauche:
                direction.turn(ANGLE_45_GAUCHE)
                moteur.drive(int(VITESSE * 0.7))
                dernier_braquage = ANGLE_45_GAUCHE
                dernier_type = "45"
            elif milieu and droite:
                direction.turn(ANGLE_45_DROITE)
                moteur.drive(int(VITESSE * 0.7))
                dernier_braquage = ANGLE_45_DROITE
                dernier_type = "45"

            # --- Virage serre (un seul cote, sans milieu) ---
            elif gauche and not milieu and not droite:
                direction.turn(ANGLE_FOND_GAUCHE)
                moteur.drive(int(VITESSE * 0.6))
                dernier_braquage = ANGLE_FOND_GAUCHE
                dernier_type = "fond"
            elif droite and not milieu and not gauche:
                direction.turn(ANGLE_FOND_DROITE)
                moteur.drive(int(VITESSE * 0.6))
                dernier_braquage = ANGLE_FOND_DROITE
                dernier_type = "fond"

        else:
            # --- Gestion de l'espace blanc (Ligne discontinue) ---
            if temps_perte is None:
                temps_perte = time.time()  # Initialisation du chronomètre au début de la coupure
            
            temps_ecoule = time.time() - temps_perte

            if temps_ecoule < DELAI_GAP_BLANC:
                # Comportement conservateur : on force les roues droites et on avance pour franchir l'interruption
                direction.turn(ANGLE_CENTRE)
                moteur.drive(VITESSE)
            else:
                # Si le délai est dépassé, la ligne est réellement perdue (fin de piste ou sortie de route)
                # On applique la stratégie de secours selon le contexte précédent le gap
                if dernier_type == "droit":
                    direction.turn(ANGLE_CENTRE)
                    moteur.reverse(VITESSE_RECUL)

                elif dernier_type == "45":
                    direction.turn(ANGLE_CENTRE)
                    moteur.reverse(VITESSE_RECUL)

                elif dernier_type == "fond":
                    # Contre-braquage pour tenter de reculer sur la dernière position connue de la ligne
                    if dernier_braquage == ANGLE_FOND_GAUCHE:
                        direction.turn(ANGLE_FOND_DROITE)
                    else:
                        direction.turn(ANGLE_FOND_GAUCHE)
                    moteur.reverse(VITESSE_RECUL)


# ==========================================================================
# MISSIONS A VENIR
# ==========================================================================
def resoudre_labyrinthe(camera, moteur, direction, feuxAvant=None):
    """Navigation dans le labyrinthe via detection de fleches. (a implementer)"""
    pass


def detecter_fleches(camera, moteur, direction, feuxAvant=None):
    """Detection de fleches directionnelles. (a implementer)"""
    pass


# ==========================================================================
# ORCHESTRATION
# ==========================================================================
def main():
    # --- Vision ---
    camera = FluxVideo(streaming=STREAMING)

    # --- Actionneurs & capteurs ---
    moteur = Moteur()
    direction = Direction()
    tourelle = Tourelle()
    capteur = CapteurSuiviLigne()
    ledArriere = FeuxArriere()
    # feuxAvant = FeuxAvant()
    feuxAvant = None

    ledArriere.set_led_brightness(0)
    ledArriere.set_all_led_rgb([0, 0, 0])
    tourelle.turnYAxis(50)

    try:
        # Mission 1 : suivre la ligne rouge jusqu'au ruban bleu
        
        # resultat = suivre_ligne_rouge(camera, moteur, direction, feuxAvant)

        resultat = suivi_ligne_noire(capteur, moteur, direction)

        # Exemple d'enchainement (a activer plus tard) :
        # if resultat == "bleu":
        #     suivi_ligne_noire(capteur, moteur, direction)

    except KeyboardInterrupt:
        print("Arret manuel")
    finally:
        tourelle.turnYAxis(0)
        moteur.destroy()
        direction.reset()
        if feuxAvant:
            feuxAvant.off()
        camera.stop()


if __name__ == "__main__":
    main()