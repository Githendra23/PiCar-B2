from picamera2 import Picamera2
import cv2
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer
from RecoFleche import RecoFleche
import threading
import time


# Paramètres pour la détection de ligne au sol
# Le rouge en HSV est à cheval sur 0 et 180, donc on utilise deux plages.
ROUGE_BAS_MIN = (0, 100, 100)
ROUGE_BAS_MAX = (10, 255, 255)
ROUGE_HAUT_MIN = (170, 100, 100)
ROUGE_HAUT_MAX = (180, 255, 255)
MIN_CONTOUR_AREA = 500  # Surface minimale pour considerer un contour comme valide


def corriger_couleurs(frame):
    """
    Convertit l'image fournie par picamera2 vers le BGR attendu par OpenCV.
    Avec cette camera, les canaux R et B sont inverses -> on les remet dans l'ordre.
    Cette conversion est faite UNE SEULE FOIS, juste apres la capture.
    """
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)


def detecter_centres_ligne_au_sol(image_bgr):
    """
    Detecte une ligne rouge au sol et retourne 2 points espaces verticalement.

    Args:
        image_bgr: Image au format BGR (deja corrigee par corriger_couleurs)

    Returns:
        tuple: (point_devant, point_derriere) ou chaque point est (x, y) ou None
    """
    try:
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

        # Le rouge occupe deux plages de teinte en HSV : on combine les deux.
        mask_rouge = cv2.inRange(hsv, ROUGE_BAS_MIN, ROUGE_BAS_MAX) \
            + cv2.inRange(hsv, ROUGE_HAUT_MIN, ROUGE_HAUT_MAX)

        mask_rouge = cv2.erode(mask_rouge, None, iterations=2)
        mask_rouge = cv2.dilate(mask_rouge, None, iterations=2)

        contours, _ = cv2.findContours(
            mask_rouge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None, None

        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) < MIN_CONTOUR_AREA:
            return None, None

        epsilon = 0.01 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)

        points = approx.squeeze()
        if len(points.shape) == 1:
            points = points.reshape(-1, 2)
        if len(points) < 2:
            return None, None

        y_coords = points[:, 1]
        point_devant = tuple(points[np.argmin(y_coords)])
        point_derriere = tuple(points[np.argmax(y_coords)])

        if abs(point_devant[1] - point_derriere[1]) < 50:
            sorted_points = points[np.argsort(points[:, 1])]
            if len(sorted_points) >= 2:
                point_devant = tuple(sorted_points[int(len(sorted_points) * 0.25)])
                point_derriere = tuple(sorted_points[int(len(sorted_points) * 0.75)])

        return point_devant, point_derriere

    except Exception as e:
        print(f"Erreur dans detecter_centres_ligne_au_sol: {e}")
        return None, None


# Creation de la camera
picam2 = Picamera2()

# Creation du detecteur de fleche
detecteur = RecoFleche()

config = picam2.create_preview_configuration(
    main={
        "size": (640, 480),
        "format": "RGB888"
    }
)

picam2.configure(config)
picam2.start()


class StreamingHandler(BaseHTTPRequestHandler):
    """Handler pour le flux avec detection de fleches."""
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
                frame = picam2.capture_array()
                image_bgr = corriger_couleurs(frame)   # couleurs remises dans l'ordre

                image_bgr, direction = detecteur.detecter(image_bgr)
                if direction != "Inconnue":
                    print("Direction detectee :", direction)

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


class SecondStreamingHandler(BaseHTTPRequestHandler):
    """Handler pour le flux avec affichage des centres de ligne."""
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
                frame = picam2.capture_array()
                image_bgr = corriger_couleurs(frame)   # couleurs remises dans l'ordre

                point_devant, point_derriere = detecter_centres_ligne_au_sol(image_bgr)

                if point_devant is not None:
                    cv2.circle(image_bgr, point_devant, 8, (0, 255, 0), -1)
                    cv2.putText(image_bgr, "P1",
                                (point_devant[0] + 15, point_devant[1]),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                if point_derriere is not None:
                    cv2.circle(image_bgr, point_derriere, 8, (0, 0, 255), -1)
                    cv2.putText(image_bgr, "P2",
                                (point_derriere[0] + 15, point_derriere[1]),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                if point_devant is not None and point_derriere is not None:
                    cv2.line(image_bgr, point_devant, point_derriere, (255, 255, 0), 2)

                success, jpeg = cv2.imencode(".jpg", image_bgr)
                if not success:
                    continue

                self.wfile.write(b"--FRAME\r\n")
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(jpeg)))
                self.end_headers()
                self.wfile.write(jpeg.tobytes())
                self.wfile.write(b"\r\n")

        except Exception as e:
            print(f"Erreur dans SecondStreamingHandler: {e}")
            pass


def run_server(server, port):
    print(f"Serveur lance sur le port {port}")
    server.serve_forever()


if __name__ == "__main__":
    try:
        serveur = HTTPServer(("0.0.0.0", 8000), StreamingHandler)
        raw_serveur = HTTPServer(("0.0.0.0", 8001), SecondStreamingHandler)

        print("Serveurs lances.")
        print("Flux avec detection de fleches : http://<IP_DU_PI>:8000")
        print("Flux avec centres de ligne     : http://<IP_DU_PI>:8001")

        threading.Thread(target=run_server, args=(serveur, 8000), daemon=True).start()
        threading.Thread(target=run_server, args=(raw_serveur, 8001), daemon=True).start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Arret des serveurs")

    finally:
        picam2.stop()