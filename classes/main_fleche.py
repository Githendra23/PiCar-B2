import time

from FluxVideo import FluxVideo, demarrer_server_video, StabilisateurDirection
from RecoFleche import RecoFleche
from NavigationLabyrinthe import NavigationLabyrinthe


if __name__ == "__main__":
    navigation = NavigationLabyrinthe()

    flux = FluxVideo()
    reco = RecoFleche()
    stabilisateur = StabilisateurDirection(
        taille_historique=7,
        minimum_validation=4
    )

    server = None

    try:
        flux.start()
        server = demarrer_server_video(flux, port=8000)

        while True:
            # 1. Lecture caméra
            image = flux.get_frame()

            # 2. Détection flèche
            image_annotee, direction_detectee = reco.detecter(image)

            # 3. Stabilisation de la direction
            direction = stabilisateur.ajouter_detection(direction_detectee)

            # 4. Mise à jour du flux vidéo annoté
            flux.set_image_stream(image_annotee)

            # 5. Sécurité obstacle devant
            distance_devant = navigation.lire_distance_stable()
            print(f"Flèche : {direction} | Distance devant : {distance_devant:.0f} mm")

            if distance_devant <= navigation.DISTANCE_STOP:
                print("Obstacle devant : sécurité obstacle")
                navigation.executer_choix("bloque")
                time.sleep(0.2)
                continue

            # 6. Action selon la flèche
            if direction == "Gauche":
                navigation.executer_choix("droite")

            elif direction == "Droite":
                navigation.executer_choix("gauche")

            else:
                # Si aucune flèche claire, on avance doucement
                navigation.executer_choix("centre")

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("Arrêt demandé par l'utilisateur")
        navigation.moteur.stop()
        navigation.direction.reset()

    finally:
        print("Arrêt propre demandé.")

        try:
            navigation.moteur.stop()
            navigation.direction.reset()
        except Exception as e:
            print(f"Erreur arrêt moteur/direction : {e}")

        try:
            if server is not None:
                server.shutdown()
                server.server_close()
        except Exception as e:
            print(f"Erreur arrêt serveur vidéo : {e}")

        try:
            flux.stop()
        except Exception as e:
            print(f"Erreur arrêt flux vidéo : {e}")

        try:
            navigation.arret_propre()
        except Exception as e:
            print(f"Erreur arrêt navigation : {e}")