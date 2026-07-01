import time

from NavigationLabyrinthe import NavigationLabyrinthe

if __name__ == "__main__":
    navigation = NavigationLabyrinthe()

    try:
        while True:
            distances = navigation.scanner_fluide()
            choix, angle, distance = navigation.choisir_angle_fluide(distances)

            navigation.afficher_scan_fluide(distances, choix, angle, distance)

            # input("Appuie sur Entrée pour exécuter l'action moteur")

            navigation.executer_choix(choix)

            # input("Appuie sur ENtrée pour refaire le scan")

            time.sleep(0.3)

    except KeyboardInterrupt:
        print("Arrêt demandé par l'utilisateur")

    finally:
        navigation.arret_propre()