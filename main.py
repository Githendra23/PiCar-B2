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
 
    Cle du probleme des virages : on braque plus FRANCHEMENT et on RALENTIT plus
    en virage, pour reagir a temps et eviter que les 3 capteurs sortent ensemble
    (ce qui serait pris a tort pour une ligne discontinue).
 
    Distinction TROU vs VIRAGE :
      - Un TROU (ligne discontinue) n'arrive que sur une portion DROITE.
      - Si on braquait (dernier_braquage != centre), une perte = sortie de virage
        -> recuperation immediate, jamais traite comme un trou.
 
    Optimisation : on n'envoie un ordre au moteur/servo que lorsqu'il CHANGE.
    """
    ANGLE_CENTRE = 90
    # Virages plus FRANCS qu'avant (on reagit plus tot/fort)
    ANGLE_45_GAUCHE = 115     # virage doux gauche  (ecart 25)
    ANGLE_45_DROITE = 65      # virage doux droite  (ecart 25)
    ANGLE_FOND_GAUCHE = 140   # virage serre gauche
    ANGLE_FOND_DROITE = 40    # virage serre droite
 
    VITESSE = 20
    VITESSE_RECUL = 15
    DELAI_GAP_BLANC = 1.2     # secondes max pour franchir un trou
 
    dernier_braquage = ANGLE_CENTRE
    temps_perte = None
 
    # Memoire des derniers ordres envoyes (pour ne renvoyer que si ca change)
    angle_actuel = None
    vitesse_actuelle = None
    sens_actuel = None        # 'avant' | 'arriere'
 
    def appliquer(angle, vitesse, sens):
        """Envoie les ordres au servo/moteur SEULEMENT s'ils ont change."""
        nonlocal angle_actuel, vitesse_actuelle, sens_actuel
        if angle != angle_actuel:
            direction.turn(angle)
            angle_actuel = angle
        if vitesse != vitesse_actuelle or sens != sens_actuel:
            if sens == "avant":
                moteur.drive(vitesse)
            else:
                moteur.reverse(vitesse)
            vitesse_actuelle = vitesse
            sens_actuel = sens
 
    while True:
        gauche, milieu, droite = capteur.getState()
        ligne_visible = (gauche or milieu or droite)
 
        if ligne_visible:
            temps_perte = None
 
            # --- Tout droit ---
            if (milieu and not gauche and not droite) \
               or (gauche and milieu and droite) \
               or (droite and gauche and not milieu):
                appliquer(ANGLE_CENTRE, VITESSE, "avant")
                dernier_braquage = ANGLE_CENTRE
 
            # --- Virage doux (milieu + un cote) : on RALENTIT bien ---
            elif milieu and gauche:
                appliquer(ANGLE_45_GAUCHE, int(VITESSE * 0.6), "avant")
                dernier_braquage = ANGLE_45_GAUCHE
            elif milieu and droite:
                appliquer(ANGLE_45_DROITE, int(VITESSE * 0.6), "avant")
                dernier_braquage = ANGLE_45_DROITE
 
            # --- Virage serre (un seul cote) : on ralentit ENCORE plus ---
            elif gauche and not milieu and not droite:
                appliquer(ANGLE_FOND_GAUCHE, int(VITESSE * 0.5), "avant")
                dernier_braquage = ANGLE_FOND_GAUCHE
            elif droite and not milieu and not gauche:
                appliquer(ANGLE_FOND_DROITE, int(VITESSE * 0.5), "avant")
                dernier_braquage = ANGLE_FOND_DROITE
 
        else:
            # --- Ligne perdue (0,0,0) ---
            # Un TROU n'arrive que si on allait DROIT. Si on braquait, c'est une
            # sortie de virage -> recuperation immediate.
            if dernier_braquage == ANGLE_CENTRE:
                # On allait droit -> peut-etre un trou -> tenter de franchir
                if temps_perte is None:
                    temps_perte = time.time()
                if time.time() - temps_perte < DELAI_GAP_BLANC:
                    appliquer(ANGLE_CENTRE, VITESSE, "avant")
                else:
                    # Trou trop long -> vraie perte -> reculer droit
                    appliquer(ANGLE_CENTRE, VITESSE_RECUL, "arriere")
            else:
                # On braquait -> sortie de virage -> contre-braquage + recul immediat
                if dernier_braquage in (ANGLE_FOND_GAUCHE, ANGLE_45_GAUCHE):
                    appliquer(ANGLE_FOND_DROITE, VITESSE_RECUL, "arriere")
                else:
                    appliquer(ANGLE_FOND_GAUCHE, VITESSE_RECUL, "arriere")
 
        time.sleep(0.01)

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