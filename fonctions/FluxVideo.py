from picamera2 import Picamera2
import cv2
from http.server import BaseHTTPRequestHandler, HTTPServer
from RecoFleche import RecoFleche


# Création de la caméra
picam2 = Picamera2()

# Création du détecteur de flèche
detecteur = RecoFleche()

# Configuration du flux vidéo
config = picam2.create_preview_configuration(
    main={
        "size": (640, 480),
        "format": "RGB888"
    }
)

picam2.configure(config)
picam2.start()


class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Fonction appelée automatiquement quand un navigateur
        se connecte à l'adresse du serveur.
        """

        if self.path != "/":
            self.send_error(404)
            return

        # Réponse HTTP correcte
        self.send_response(200)
        self.send_header("Age", 0)
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")

        # Type spécial pour envoyer plusieurs images JPEG à la suite
        self.send_header(
            "Content-Type",
            "multipart/x-mixed-replace; boundary=FRAME"
        )

        self.end_headers()

        try:
            while True:
                # Capture d'une image depuis la caméra
                image = picam2.capture_array()

                # Analyse de l'image avec la classe RecoFleche
                image, direction = detecteur.detecter(image)

                # Affichage terminal uniquement si une direction est trouvée
                if direction != "Inconnue":
                    print("Direction détectée :", direction)

                # Conversion RGB vers BGR pour OpenCV
                image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                # Encodage de l'image en JPEG
                success, jpeg = cv2.imencode(".jpg", image_bgr)

                if not success:
                    continue

                # Envoi de l'image JPEG au navigateur
                self.wfile.write(b"--FRAME\r\n")
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(jpeg)))
                self.end_headers()
                self.wfile.write(jpeg.tobytes())
                self.wfile.write(b"\r\n")

        except Exception:
            pass


try:
    # 0.0.0.0 permet d'accéder au serveur depuis ton PC
    serveur = HTTPServer(("0.0.0.0", 8000), StreamingHandler)

    print("Serveur lancé.")
    print("Ouvre cette adresse dans ton navigateur :")
    print("http://10.101.2.116:8000")

    serveur.serve_forever()

except KeyboardInterrupt:
    print("Arrêt du serveur")

finally:
    picam2.stop()