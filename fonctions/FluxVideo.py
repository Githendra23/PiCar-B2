from picamera2 import Picamera2
import cv2
from http.server import BaseHTTPRequestHandler, HTTPServer
from RecoFleche import RecoFleche
import threading


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
    """Handler pour le flux avec détection de flèches."""
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Age", 0)
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header(
            "Content-Type",
            "multipart/x-mixed-replace; boundary=FRAME"
        )
        self.end_headers()

        try:
            while True:
                image = picam2.capture_array()
                image, direction = detecteur.detecter(image)

                if direction != "Inconnue":
                    print("Direction détectée :", direction)

                image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                success, jpeg = cv2.imencode(".jpg", image_bgr)

                if not success:
                    continue

                self.wfile.write(b"--FRAME\r\n")
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(jpeg)))
                self.end_headers()
                self.wfile.write(jpeg.tobytes())
                self.wfile.write(b"\r\n")

        except Exception:
            pass


class RawStreamingHandler(BaseHTTPRequestHandler):
    """Handler pour le flux brut, sans détection."""
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Age", 0)
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header(
            "Content-Type",
            "multipart/x-mixed-replace; boundary=FRAME"
        )
        self.end_headers()

        try:
            while True:
                image = picam2.capture_array()
                image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                success, jpeg = cv2.imencode(".jpg", image_bgr)

                if not success:
                    continue

                self.wfile.write(b"--FRAME\r\n")
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(jpeg)))
                self.end_headers()
                self.wfile.write(jpeg.tobytes())
                self.wfile.write(b"\r\n")

        except Exception:
            pass


def run_server(server, port):
    print(f"Serveur lancé sur le port {port}")
    server.serve_forever()


if __name__ == "__main__":
    try:
        serveur = HTTPServer(("0.0.0.0", 8000), StreamingHandler)
        raw_serveur = HTTPServer(("0.0.0.0", 8001), RawStreamingHandler)

        print("Serveurs lancés.")
        print("Flux avec détection : http://10.101.2.116:8000")
        print("Flux brut : http://10.101.2.116:8001")

        # Lance les serveurs dans des threads séparés
        threading.Thread(target=run_server, args=(serveur, 8000), daemon=True).start()
        threading.Thread(target=run_server, args=(raw_serveur, 8001), daemon=True).start()

        # Garde le programme en vie
        while True:
            pass

    except KeyboardInterrupt:
        print("Arrêt des serveurs")

    finally:
        picam2.stop()
