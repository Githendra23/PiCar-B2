import time
from classes.Roues import Roues
from classes.ServoController import ServoController
from classes.CapteurSuiviLigne import CapteurSuiviLigne
from classes.Moteur import m1, map as motor_map

VITESSE_BASE   = 60
VITESSE_MIN    = 30
VITESSE_RECHERCHE   = 35

# Table : statut -> (delta_angle, facteur_vitesse)
COMPORTEMENTS = {
    (1, 1, 1): (  0, 1.00),   # centré
    (0, 1, 1): (+15, 0.90),   # légère dérive droite
    (0, 0, 1): (+30, 0.70),   # forte dérive droite
    (1, 1, 0): (-15, 0.90),   # légère dérive gauche
    (1, 0, 0): (-30, 0.70),   # forte dérive gauche
}

def set_throttle(vitesse_pct):
    """Applique directement le throttle sans boucle bloquante."""
    vitesse_pct = max(0, min(vitesse_pct, 100))
    m1.moteur.throttle = motor_map(vitesse_pct, 0, 100, 0, 1.0)

def suivi_ligne():
    capteur = CapteurSuiviLigne()
    roues   = Roues(ServoController())
    centre  = roues.getAngleCenter()

    delta_courant = 0

    print("Démarrage suivi de ligne...")
    set_throttle(VITESSE_BASE)

    try:
        while True:
            statut = capteur.statut()

            if statut in COMPORTEMENTS:
                delta, facteur = COMPORTEMENTS[statut]
                delta_courant = delta
                vitesse = max(VITESSE_MIN, VITESSE_BASE * facteur)
            else:
               
                delta   = delta_courant
                vitesse = VITESSE_RECHERCHE
                print(f"Ligne perdue ! Maintien delta={delta}")

            angle = centre + delta
            angle = max(roues.getAngleMin(), min(angle, roues.getAngleMax()))

            roues.turn(angle)
            set_throttle(vitesse)

            print(f"statut={statut}  angle={angle}  vitesse={vitesse:.0f}%")
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Arrêt demandé.")
    finally:
        set_throttle(0)
        roues.reset()
        m1.destroy()

if __name__ == "__main__":
    suivi_ligne()
