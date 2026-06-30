import time

from NavigationLabyrinthe import NavigationLabyrinthe

if __name__ == "__main__":
    navigation = NavigationLabyrinthe()

    try:
        while True:
            distances = navigation.scanner_directions()
            choix = navigation.choisir_direction(distances)

            navigation.afficher_scan(distances, choix)

            time.sleep(1.5)

    except KeyboardInterrupt:
        print("Arrêt demandé par l'utilisateur")

    finally:
        navigation.arret_propre()