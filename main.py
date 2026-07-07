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

# --- Suivi de ligne NOIRE (capteur IR) : angles de braquage ---
# Convention servo : turn(0) = droite, turn(90) = centre, turn(130) = gauche
ANGLE_CENTRE = 90
ANGLE_45_GAUCHE = 100     # virage doux gauche
ANGLE_45_DROITE = 70      # virage doux droite
ANGLE_FOND_GAUCHE = 130   # virage serre gauche
ANGLE_FOND_DROITE = 50     # virage serre droite
VITESSE_RECUL = 15
DELAI_AVANT_RECUL = 2.0   # secondes tout droit avant de reculer (perte en ligne droite)

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
    Suit une ligne noire avec les 3 capteurs IR via une regulation incrementale.
    L'angle de direction est ajuste progressivement pour eviter les a-coups.
    """
    # Parametres de regulation angulaire
    PAS_DOUX = 2            # Incrément pour une erreur legere
    PAS_FORT = 10            # Incrément pour une erreur forte
    PAS_RETOUR = 3          # Incrément pour le retour au centre
    DELAI_MAJ = 0.02        # Delai (s) entre chaque calcul d'increment (20ms)

    angle_courant = ANGLE_CENTRE
    dernier_braquage_dir = "centre"   # Memorise le sens pour la recuperation ('gauche', 'droite')
    dernier_type = "droit"            # Memorise l'intensite de la courbe ('droit', '45', 'fond')
    temps_perte = None
    dernier_temps_maj = time.time()

    VITESSE = 25
    VITESSE_RECUL = 15

    direction.turn(angle_courant)

    while True:
        gauche, milieu, droite = capteur.getState()
        ligne_visible = (gauche or milieu or droite)
        maintenant = time.time()

        if ligne_visible:
            temps_perte = None

            # Execution de la regulation a intervalle regulier pour controler la vitesse de braquage
            if maintenant - dernier_temps_maj >= DELAI_MAJ:
                
                # --- Alignement correct (centre ou 3 capteurs) ---
                if (milieu and not gauche and not droite) or (gauche and milieu and droite):
                    # Retour progressif vers l'angle central
                    if angle_courant > ANGLE_CENTRE:
                        angle_courant = max(ANGLE_CENTRE, angle_courant - PAS_RETOUR)
                    elif angle_courant < ANGLE_CENTRE:
                        angle_courant = min(ANGLE_CENTRE, angle_courant + PAS_RETOUR)
                    
                    dernier_type = "droit"
                    dernier_braquage_dir = "centre"

                # --- Ecart leger (milieu + un cote) ---
                elif milieu and gauche:
                    angle_courant = min(ANGLE_FOND_GAUCHE, angle_courant + PAS_DOUX)
                    dernier_type = "45"
                    dernier_braquage_dir = "gauche"
                    
                elif milieu and droite:
                    angle_courant = max(ANGLE_FOND_DROITE, angle_courant - PAS_DOUX)
                    dernier_type = "45"
                    dernier_braquage_dir = "droite"

                # --- Ecart important (un seul cote) ---
                elif gauche and not milieu and not droite:
                    angle_courant = min(ANGLE_FOND_GAUCHE, angle_courant + PAS_FORT)
                    dernier_type = "fond"
                    dernier_braquage_dir = "gauche"
                    
                elif droite and not milieu and not gauche:
                    angle_courant = max(ANGLE_FOND_DROITE, angle_courant - PAS_FORT)
                    dernier_type = "fond"
                    dernier_braquage_dir = "droite"

                dernier_temps_maj = maintenant

            # Application de l'angle calcule
            direction.turn(angle_courant)

            # Ajustement dynamique de la vitesse selon la contrainte de la trajectoire
            if dernier_type == "droit":
                moteur.drive(VITESSE)
            elif dernier_type == "45":
                moteur.drive(int(VITESSE * 0.8))
            elif dernier_type == "fond":
                moteur.drive(int(VITESSE * 0.65))

        else:
            # --- Strategie de recuperation (ligne perdue) ---
            if temps_perte is None:
                temps_perte = maintenant
            temps_ecoule = maintenant - temps_perte

            if dernier_type == "droit":
                if temps_ecoule < DELAI_AVANT_RECUL:
                    direction.turn(ANGLE_CENTRE)
                    moteur.drive(VITESSE)
                else:
                    direction.turn(ANGLE_CENTRE)
                    moteur.reverse(VITESSE_RECUL)

            elif dernier_type == "45":
                direction.turn(ANGLE_CENTRE)
                moteur.reverse(VITESSE_RECUL)

            elif dernier_type == "fond":
                # Braquage maximal oppose pour rattraper l'angle de fuite
                if dernier_braquage_dir == "gauche":
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