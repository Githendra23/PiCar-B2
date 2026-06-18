# Mes classes
import CapteurUltrason
import LEDAvant
import Moteur

# Des librairies nécessaires
import sys
import time
import threading


# Initialisation du matériel
moteur = Moteur.Moteur()
capteurUltrason = CapteurUltrason.CapteurUltrason()
ledAvant = LEDAvant.LEDAvant()


caractere = '0'
programme_actif = True

# Fonction pour lire sur le clavier
def lire_clavier():
    global caractere, programme_actif

    while programme_actif:
        caractere = input("M pour avancer")
        print(f"Caractère reçu : {caractere}")


if __name__ == "__main__":
    vitesse = 30

    try:
        # On lance un thread pour simuler une lecture asynchrone sur le clavier
        threading.Thread(target=lire_clavier, daemon=True).start()

        while True:
            distance = capteurUltrason.distance()
            capteurUltrason.afficher_distance()

            # En fonction des différentes entrées sur le clavier, on avance/stoppe le moteur.
            # Si un obstacle se trouve à moins de 25cm du robot, on stoppe le moteur, et on allume les warnings.
            if caractere == 'A' or caractere == 'a' or distance <= 250:
                moteur.stop()
                ledAvant.warning()
            elif caractere == 'M' or caractere == 'm': # Si on souhaite avancer
                moteur.avancer(vitesse)
            elif caractere == 'S' or caractere == 's': # Si on souhaite reculer
                moteur.reculer(vitesse)
            elif caractere == 'Q' or caractere == 'q': # Si on souhaite terminer le programme
                print("Arrêt demandé.")
                break

            time.sleep(0.01)
    except KeyboardInterrupt: # Si on fait Ctrl+C sur le clavier pour terminer le programme
        print("Programme interrompu via le clavier.")
    finally:
        programme_actif = False
        moteur.destroy()