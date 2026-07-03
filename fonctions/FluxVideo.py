from picamera2 import Picamera2
import cv2
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import math
import time
import socket
import os
import sys


CHEMIN_CLASSES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "classes")
sys.path.append(CHEMIN_CLASSES)

from Moteur import Moteur
from Direction import Direction

# Plages de detection du rouge en HSV (deux zones car le rouge est a cheval sur 0/180)
ROUGE_BAS_MIN = (0, 100, 100)
ROUGE_BAS_MAX = (10, 255, 255)
ROUGE_HAUT_MIN = (170, 100, 100)
ROUGE_HAUT_MAX = (180, 255, 255)
MIN_CONTOUR_AREA = 500

# Ruban BLEU (arret)
BLEU_MIN = (100, 100, 100)
BLEU_MAX = (130, 255, 255)
BLEU_AIRE_ARRET = 3000      # surface bleue minimale pour declencher l'arret
BLEU_ZONE_BAS = 300         # on ne regarde le bleu que sous cette ligne (proche du robot)

# Parametres de pilotage (a ajuster au test)
CENTRE_IMAGE = 320          # 640 / 2 : l'axe du robot dans l'image
ZONE_MORTE = 40             # marge d'erreur (px) : en dessous -> robot considere centre
GAIN = 0.15                 # force du braquage (plus grand = braque plus fort)
SENS_SERVO = 1              # 1 ou -1 : a inverser si le robot braque du mauvais cote
VITESSE = 25                # vitesse d'avance (faible : transmission fragile)

# Etat partage pour le flux web (le web ne fait que regarder)
etat_partage = {"jpeg": None}
verrou = threading.Lock()


def obtenir_ip_locale():
    """Retourne l'IP locale actuelle du Raspberry Pi (peu importe le reseau)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # pas de vrai trafic envoye, juste pour choisir l'interface
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


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


def position_ligne_rouge(image_bgr):
    """Retourne la position x du centre de la ligne rouge, ou None."""
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, ROUGE_BAS_MIN, ROUGE_BAS_MAX) \
        + cv2.inRange(hsv, ROUGE_HAUT_MIN, ROUGE_HAUT_MAX)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < MIN_CONTOUR_AREA:
        return None

    M = cv2.moments(largest)
    if M["m00"] == 0:
        return None
    return int(M["m10"] / M["m00"])


def bleu_proche(image_bgr):
    """Retourne True si une zone bleue suffisante est proche (bas de l'image)."""
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, BLEU_MIN, BLEU_MAX)
    mask[:BLEU_ZONE_BAS, :] = 0          # on ignore le haut de l'image
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False
    largest = max(contours, key=cv2.contourArea)
    return cv2.contourArea(largest) > BLEU_AIRE_ARRET


def calculer_angle(point_devant, point_derriere):
    """
    Angle de la ligne par rapport a la verticale (en degres).
      0  = ligne droite devant
      >0 = ligne penche a droite
      <0 = ligne penche a gauche
    """
    dx = point_devant[0] - point_derriere[0]
    dy = point_devant[1] - point_derriere[1]   # negatif car 'devant' est plus haut
    angle = math.degrees(math.atan2(dx, -dy))
    return angle


picam2 = Picamera2()
# CORRECTION : Utilisation du format BGR888 natif pour eviter l'inversion des canaux rouge et bleu
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "BGR888"}
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
                with verrou:
                    jpeg = etat_partage["jpeg"]
                if jpeg is None:
                    time.sleep(0.05)
                    continue
                self.wfile.write(b"--FRAME\r\n")
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(jpeg)))
                self.end_headers()
                self.wfile.write(jpeg.tobytes())
                self.wfile.write(b"\r\n")
                time.sleep(0.03)
        except Exception:
            pass

    def log_message(self, *args):
        pass


def lancer_serveur_web():
    serveur = HTTPServer(("0.0.0.0", 8000), StreamingHandler)
    print(f"Flux video : http://{obtenir_ip_locale()}:8000")
    serveur.serve_forever()


def publier(image_bgr):
    success, jpeg = cv2.imencode(".jpg", image_bgr)
    if success:
        with verrou:
            etat_partage["jpeg"] = jpeg


if __name__ == "__main__":
    # Le serveur web tourne dans son propre thread (independant du controle)
    threading.Thread(target=lancer_serveur_web, daemon=True).start()

    moteur = Moteur()
    direction = Direction()

    try:
        while True:
            # Partie camera IDENTIQUE a ton code d'origine (couleur inchangee)
            image_bgr = cv2.cvtColor(picam2.capture_array(), cv2.COLOR_RGB2BGR)

            # 1) PRIORITE : ruban bleu proche -> on s'arrete et on termine
            if bleu_proche(image_bgr):
                moteur.stop()
                direction.reset()
                cv2.putText(image_bgr, "STOP (bleu detecte)", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                publier(image_bgr)
                print("Ruban bleu detecte -> arret")
                break

            # 2) Suivi de la ligne rouge
            x_ligne = position_ligne_rouge(image_bgr)

            if x_ligne is None:
                # Ligne perdue -> arret de securite
                moteur.stop()
                cv2.putText(image_bgr, "Ligne non detectee", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            else:
                erreur = x_ligne - CENTRE_IMAGE

                if abs(erreur) < ZONE_MORTE:
                    # Dans la marge -> tout droit
                    angle = direction.getAngleCenter()
                else:
                    # Braquage proportionnel a l'ecart pour recentrer la ligne
                    angle = direction.getAngleCenter() - SENS_SERVO * (erreur * GAIN)
                    angle = max(direction.getAngleMin(),
                                min(direction.getAngleMax(), angle))

                direction.turn(int(angle))
                moteur.drive(VITESSE)

                # Affichage debug sur le flux
                cv2.line(image_bgr, (CENTRE_IMAGE, 0), (CENTRE_IMAGE, 480), (0, 255, 0), 1)
                cv2.circle(image_bgr, (x_ligne, 400), 8, (0, 0, 255), -1)
                cv2.putText(image_bgr, f"erreur: {erreur}  angle: {int(angle)}",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            publier(image_bgr)

    except KeyboardInterrupt:
        print("Arret manuel")
    finally:
        moteur.destroy()
        direction.reset()
        picam2.stop()