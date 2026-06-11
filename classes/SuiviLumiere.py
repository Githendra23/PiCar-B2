import time
import threading

import CapteurUltrason
import CapteurLumiere
import LEDAvant
import Moteur
import Servos

# ======================
# Réglages à adapter
# ======================
DISTANCE_OBSTACLE_MM = 200      # 20 cm

VITESSE_AVANCE = 50
VITESSE_RECUL = 25              # vitesse réduite
TEMPS_RECUL = 1.2               # à ajuster pour obtenir environ 30 cm
TEMPS_ARRET_APRES_OBSTACLE = 2.0
TEMPS_DETRESSE = 1.0

# Canaux du capteur de lumière sur le PCF8591.
# Si les valeurs ne correspondent pas, tester 0/1, 1/2, 2/3 selon le branchement.
CH_LUMIERE = 1

SEUIL_BAS = 45
SEUIL_HAUT = 95

# Mettre False si la valeur analogique baisse quand on éclaire le capteur.
VALEUR_PLUS_GRANDE_QUAND_PLUS_LUMINEUX = True

# Servo de direction.
SERVO_DIRECTION_CHANNEL = 0
ANGLE_CENTRE = 90
ANGLE_GAUCHE = 60
ANGLE_DROITE = 120

# Si le robot tourne à droite quand la lumière est à gauche, passer cette valeur à True.
INVERSER_DIRECTION = False

# Écart minimal entre les 2 capteurs pour décider de tourner.
SEUIL_ECART_LUMIERE = 20

# Durée entre deux décisions dans la boucle principale.
DELAI_BOUCLE = 0.05


# ======================
# Objets des classes
# ======================
# Dans Moteur.py, l'objet moteur est déjà créé sous le nom m1.
# On l'utilise directement, au lieu de faire Moteur.Moteur(), car le constructeur
# de la classe Moteur demande un moteur en paramètre.
moteur = Moteur.m1
capteur_ultrason = CapteurUltrason.CapteurUltrason()
capteur_lumiere = CapteurLumiere.CapteurLumiere()
led_avant = LEDAvant.LEDAvant()
servo_direction = Servos.ServoController(i2c_address=0x5f)
servo_direction.add_servo(channel=SERVO_DIRECTION_CHANNEL)


caractere = ""
mode_suivi = False
programme_actif = True
verrou = threading.Lock()
dernier_angle = None


def lire_clavier():
    """Lit M/A/Q sans bloquer la boucle principale du robot."""
    global caractere, mode_suivi, programme_actif

    while programme_actif:
        try:
            commande = input("Commande (M=marche, A=arrêt, Q=quitter) : ").strip()
        except EOFError:
            break

        if not commande:
            continue

        commande = commande[0]

        with verrou:
            caractere = commande
            if commande in ("M", "m"):
                mode_suivi = True
            elif commande in ("A", "a"):
                mode_suivi = False
            elif commande in ("Q", "q"):
                mode_suivi = False
                programme_actif = False

        print(f"Caractère reçu : {commande}")


def etat_commande():
    with verrou:
        return caractere, mode_suivi, programme_actif


def commande_arret_ou_quitter():
    commande, suivi, actif = etat_commande()
    return (not actif) or commande in ("A", "a", "Q", "q") or not suivi


def convertir_vitesse(vitesse):
    """Transforme une vitesse 0-100 en throttle 0.0-1.0."""
    vitesse = Moteur.check_speed(vitesse)
    return Moteur.map(vitesse, 0, 100, 0, 1.0)


def avancer(vitesse):
    # On n'appelle pas moteur.avancer(), car dans Moteur.py cette méthode contient
    # un while True et bloque donc tout le reste du programme.
    moteur.moteur.throttle = convertir_vitesse(vitesse)


def reculer(vitesse):
    # Même raison : on évite moteur.reculer() pour garder le contrôle de la boucle.
    moteur.moteur.throttle = -convertir_vitesse(vitesse)


def stopper():
    moteur.moteur.throttle = 0


def mettre_direction(angle):
    global dernier_angle

    if dernier_angle != angle:
        servo_direction.set_angle(SERVO_DIRECTION_CHANNEL, angle)
        dernier_angle = angle


def eteindre_detresse():
    led_avant.switch(24)  # L_R off
    led_avant.switch(25)  # L_G off
    led_avant.switch(27)  # R_R off
    led_avant.switch(28)  # R_G off


def pause_annulable(duree):
    """Attend, mais s'arrête immédiatement si A ou Q est reçu."""
    fin = time.time() + duree
    while time.time() < fin:
        if commande_arret_ou_quitter():
            return False
        time.sleep(0.02)
    return True


def detresse_pendant(duree):
    """
    Feux de détresse pendant une durée donnée.
    On ne lance pas led_avant.warning(), car cette méthode contient un while True.
    """
    fin = time.time() + duree
    allume = True

    while time.time() < fin:
        if commande_arret_ou_quitter():
            break

        if allume:
            led_avant.switch(14)  # L_R on
            led_avant.switch(15)  # L_G on
            led_avant.switch(17)  # R_R on
            led_avant.switch(18)  # R_G on
        else:
            eteindre_detresse()

        allume = not allume
        time.sleep(0.25)

    eteindre_detresse()


def valeur_lumiere(channel):
    valeur = capteur_lumiere.analogRead(channel)
    if VALEUR_PLUS_GRANDE_QUAND_PLUS_LUMINEUX:
        return valeur
    return 255 - valeur


def suivre_lumiere():
    """
    Lit la valeur unique du module Light Tracking.
    - valeur normale autour de 60-80 : centre
    - valeur haute > 95 : LDR1
    - valeur basse < 45 : LDR2
    """
    lumiere = capteur_lumiere.analogRead(CH_LUMIERE)

    if lumiere > SEUIL_HAUT:
        angle = ANGLE_GAUCHE

    elif lumiere < SEUIL_BAS:
        angle = ANGLE_DROITE

    else:
        angle = ANGLE_CENTRE

    if INVERSER_DIRECTION:
        if angle == ANGLE_GAUCHE:
            angle = ANGLE_DROITE
        elif angle == ANGLE_DROITE:
            angle = ANGLE_GAUCHE

    mettre_direction(angle)
    avancer(VITESSE_AVANCE)

    return lumiere, angle


def gerer_obstacle():
    """Arrêt, détresse, recul, pause, puis reprise automatique si M est toujours actif."""
    print("Obstacle détecté : arrêt du robot")
    stopper()
    mettre_direction(ANGLE_CENTRE)

    detresse_pendant(TEMPS_DETRESSE)

    if commande_arret_ou_quitter():
        stopper()
        return

    print("Recul du robot")
    reculer(VITESSE_RECUL)
    pause_annulable(TEMPS_RECUL)
    stopper()

    if commande_arret_ou_quitter():
        return

    print("Pause avant reprise du suivi de lumière")
    pause_annulable(TEMPS_ARRET_APRES_OBSTACLE)


if __name__ == "__main__":
    dernier_affichage = 0

    try:
        mettre_direction(ANGLE_CENTRE)
        threading.Thread(target=lire_clavier, daemon=True).start()

        print("Programme prêt. Envoie M pour démarrer, A pour arrêter, Q pour quitter.")

        while True:
            commande, suivi, actif = etat_commande()

            if not actif or commande in ("Q", "q"):
                print("Arrêt demandé.")
                break

            if commande in ("A", "a") or not suivi:
                stopper()
                mettre_direction(ANGLE_CENTRE)
                time.sleep(DELAI_BOUCLE)
                continue

            distance = capteur_ultrason.distance()

            if distance <= DISTANCE_OBSTACLE_MM:
                gerer_obstacle()
                continue

            lumiere, angle = suivre_lumiere()

            # Affichage limité pour ne pas saturer le terminal.
            if time.time() - dernier_affichage > 0.5:
                print(
                    f"distance={distance:.0f} mm | "
                    f"Light tracking value: {lumiere} | "
                    f"angle={angle}"
                )
                dernier_affichage = time.time()

            time.sleep(DELAI_BOUCLE)

    except KeyboardInterrupt:
        print("Programme interrompu via le clavier.")

    finally:
        programme_actif = False
        stopper()
        mettre_direction(ANGLE_CENTRE)
        eteindre_detresse()

        try:
            servo_direction.pca.deinit()
        except Exception:
            pass

        try:
            moteur.destroy()
        except Exception:
            pass
