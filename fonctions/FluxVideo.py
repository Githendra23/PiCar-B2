from picamera2 import Picamera2
import cv2
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer
import math
import time

# Plages de detection du rouge en HSV (deux zones car le rouge est a cheval sur 0/180)
ROUGE_BAS_MIN = (0, 100, 100)
ROUGE_BAS_MAX = (10, 255, 255)
ROUGE_HAUT_MIN = (170, 100, 100)
ROUGE_HAUT_MAX = (180, 255, 255)
MIN_CONTOUR_AREA = 500


def detecter_centres_ligne_au_sol(image_bgr):
    """Retourne 2 points (devant, derriere) sur la ligne, ou (None, None)."""
    try:
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, ROUGE_BAS_MIN, ROUGE_BAS_MAX) \
            + cv2.inRange(hsv, ROUGE_HAUT_MIN, ROUGE_HAUT_MAX)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None

        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < MIN_CONTOUR_AREA:
            return None, None

        epsilon = 0.01 * cv2.arcLength(largest, True)
        approx = cv2.approxPolyDP(largest, epsilon, True)
        points = approx.squeeze()
        if len(points.shape) == 1:
            points = points.reshape(-1, 2)
        if len(points) < 2:
            return None, None

        y = points[:, 1]
        point_devant = tuple(points[np.argmin(y)])    # le plus haut dans l'image
        point_derriere = tuple(points[np.argmax(y)])  # le plus bas dans l'image

        if abs(point_devant[1] - point_derriere[1]) < 50:
            tries = points[np.argsort(points[:, 1])]
            if len(tries) >= 2:
                point_devant = tuple(tries[int(len(tries) * 0.25)])
                point_derriere = tuple(tries[int(len(tries) * 0.75)])

        return point_devant, point_derriere
    except Exception as e:
        print(f"Erreur detection: {e}")
        return None, None


def calculer_angle(point_devant, point_derriere):
    """
    Angle de la ligne par rapport a la verticale (en degres).
      0  = ligne droite devant
      >0 = ligne penche a droite
      <0 = ligne penche a gauche
    """
    dx = point_devant[0] - point_derriere[0]
    dy = point_devant[1] - point_derriere[1]   # negatif car 'devant' est plus haut
    # atan2(dx, -dy) : -dy pour que la verticale (vers le haut) donne 0
    angle = math.degrees(math.atan2(dx, -dy))
    return angle


picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()


class StreamingHandler(BaseHTTPRequestHandler):
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
                # CORRECTION : sur cette camera, RGB888 fournit deja des donnees
                # dans l'ordre BGR attendu par OpenCV. Aucune conversion couleur
                # n'est necessaire (on a verifie : ajouter cvtColor faisait
                # apparaitre le rouge en bleu -> c'etait une inversion en trop).
                image_bgr = picam2.capture_array()

                point_devant, point_derriere = detecter_centres_ligne_au_sol(image_bgr)

                if point_devant is not None and point_derriere is not None:
                    # Points
                    cv2.circle(image_bgr, point_devant, 8, (0, 255, 0), -1)
                    cv2.circle(image_bgr, point_derriere, 8, (0, 0, 255), -1)

                    # Ligne qui suit l'orientation des 2 points
                    cv2.line(image_bgr, point_derriere, point_devant, (255, 255, 0), 3)

                    # Angle de la ligne
                    angle = calculer_angle(point_devant, point_derriere)
                    cv2.putText(image_bgr, f"Angle: {angle:.1f} deg",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                                0.8, (255, 255, 255), 2)

                    # Indication de direction
                    if angle > 10:
                        sens = "-> DROITE"
                    elif angle < -10:
                        sens = "<- GAUCHE"
                    else:
                        sens = "TOUT DROIT"
                    cv2.putText(image_bgr, sens, (10, 65),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                else:
                    cv2.putText(image_bgr, "Ligne non detectee", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

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


if __name__ == "__main__":
    try:
        serveur = HTTPServer(("0.0.0.0", 8000), StreamingHandler)
        print("Flux ligne + angle : http://<IP_DU_PI>:8000")
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("Arret")
    finally:
        picam2.stop()