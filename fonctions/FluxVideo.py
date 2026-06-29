from picamera2 import Picamera2
import cv2
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

# La camera est configuree en BGR888 : picamera2 fournit alors directement
# l'ordre BGR attendu par OpenCV, donc AUCUNE conversion n'est necessaire.
# C'est la facon la plus fiable d'avoir les bonnes couleurs.
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "BGR888"}
)
picam2.configure(config)
picam2.start()


class StreamingHandler(BaseHTTPRequestHandler):
    """Flux video brut, couleurs correctes, sans aucun filtre."""
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Age", 0)
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
        self.end_headers()

        try:
            while True:
                frame = picam2.capture_array()   # deja en BGR -> aucune conversion
                success, jpeg = cv2.imencode(".jpg", frame)
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


if __name__ == "__main__":
    try:
        serveur = HTTPServer(("0.0.0.0", 8000), StreamingHandler)
        print("Flux video : http://<IP_DU_PI>:8000")
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("Arret")
    finally:
        picam2.stop()