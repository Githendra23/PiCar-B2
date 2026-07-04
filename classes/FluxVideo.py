from picamera2 import Picamera2
import cv2
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import deque, Counter
import threading
import time


class StabilisateurDirection:
    def __init__(self, taille_historique=7, minimum_validation=4):
        self.historique = deque(maxlen=taille_historique)
        self.minimum_validation = minimum_validation
        self.direction_stable = "Inconnue"

    def ajouter_detection(self, direction_detectee):
        self.historique.append(direction_detectee)

        compteur = Counter(self.historique)

        nb_gauche = compteur["Gauche"]
        nb_droite = compteur["Droite"]
        nb_inconnue = compteur["Inconnue"]

        if nb_gauche >= self.minimum_validation:
            self.direction_stable = "Gauche"
        elif nb_droite >= self.minimum_validation:
            self.direction_stable = "Droite"
        elif nb_inconnue >= self.minimum_validation:
            self.direction_stable = "Inconnue"

        return self.direction_stable


class FluxVideo:
    def __init__(self, largeur=640, hauteur=480):
        self.largeur = largeur
        self.hauteur = hauteur

        self.picam2 = Picamera2()

        config = self.picam2.create_preview_configuration(
            main={
                "size": (self.largeur, self.hauteur),
                "format": "RGB888"
            }
        )

        self.picam2.configure(config)

        self.est_demarre = False
        self.derniere_image = None
        self.lock = threading.Lock()

    def start(self):
        if not self.est_demarre:
            self.picam2.start()
            self.est_demarre = True
            time.sleep(0.5)

    def get_frame(self):
        if not self.est_demarre:
            self.start()

        image = self.picam2.capture_array()

        with self.lock:
            self.derniere_image = image.copy()

        return image

    def set_image_stream(self, image):
        with self.lock:
            self.derniere_image = image.copy()

    def get_image_stream(self):
        with self.lock:
            if self.derniere_image is not None:
                return self.derniere_image.copy()

        return self.get_frame()

    def stop(self):
        if self.est_demarre:
            self.picam2.stop()
            self.est_demarre = False


def creer_handler(flux_video):
    class StreamingHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/":
                self.send_error(404)
                return

            self.send_response(200)
            self.send_header("Age", "0")
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header(
                "Content-Type",
                "multipart/x-mixed-replace; boundary=FRAME"
            )
            self.end_headers()

            try:
                while True:
                    image = flux_video.get_image_stream()

                    success, jpeg = cv2.imencode(".jpg", image)

                    if not success:
                        continue

                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(jpeg)))
                    self.end_headers()
                    self.wfile.write(jpeg.tobytes())
                    self.wfile.write(b"\r\n")

                    time.sleep(0.03)

            except Exception as erreur:
                print("Erreur dans le flux vidéo :", erreur)

    return StreamingHandler


def demarrer_server_video(flux_video, host="0.0.0.0", port=8000):
    handler = creer_handler(flux_video)
    server = HTTPServer((host, port), handler)

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )

    thread.start()

    print("Server vidéo lancé")
    print("Adresse : http://ADRESSE_IP_DE_LA_RASPBERRY:%s" % port)
    print("Pour connaître l'adresse IP : hostname -I")

    return server


if __name__ == "__main__":
    flux = FluxVideo()
    server = None

    try:
        flux.start()
        server = demarrer_server_video(flux, port=8000)

        while True:
            image = flux.get_frame()

            cv2.putText(
                image,
                "FluxVideo.py test",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            flux.set_image_stream(image)
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Arrêt du server vidéo")

    finally:
        if server is not None:
            server.shutdown()
            server.server_close()

        flux.stop()


