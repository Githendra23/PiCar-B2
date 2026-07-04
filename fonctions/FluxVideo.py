from picamera2 import Picamera2
import cv2
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import math
import time
import socket

# ==========================================================================
# PARAMETRES DE DETECTION (a ajuster au test)
# ==========================================================================
# Ligne ROUGE (le rouge est a cheval sur 0 et 180 en HSV -> deux plages)
ROUGE_BAS_MIN = (0, 100, 100)
ROUGE_BAS_MAX = (10, 255, 255)
ROUGE_HAUT_MIN = (170, 100, 100)
ROUGE_HAUT_MAX = (180, 255, 255)
MIN_CONTOUR_AREA = 500

# Ruban BLEU (arret)
BLEU_MIN = (100, 100, 100)
BLEU_MAX = (130, 255, 255)
BLEU_AIRE_ARRET = 3000
BLEU_ZONE_BAS = 300

CENTRE_IMAGE = 320          # 640 / 2 : l'axe du robot dans l'image


class FluxVideo:
    """
    Gere la camera, la detection (ligne rouge + ruban bleu) et le serveur web.
    NE PILOTE PAS le robot : elle ne fait que "voir" et renvoyer les infos au main.

    Methode principale : analyser() -> dictionnaire d'infos pour le main.
    """

    def __init__(self, taille=(640, 480), port_web=8000, streaming=False):
        self.largeur, self.hauteur = taille
        self.port_web = port_web
        self.centre_image = CENTRE_IMAGE

        # Camera
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": taille, "format": "BGR888"}
        )
        self.picam2.configure(config)
        self.picam2.start()

        # Streaming web (optionnel)
        self.streaming_actif = False
        self._jpeg = None
        self._verrou = threading.Lock()
        if streaming:
            self.demarrer_streaming()

    # ------------------------------------------------------------------
    # DETECTION (methodes internes)
    # ------------------------------------------------------------------
    def _masque_rouge(self, image_bgr):
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, ROUGE_BAS_MIN, ROUGE_BAS_MAX) \
            + cv2.inRange(hsv, ROUGE_HAUT_MIN, ROUGE_HAUT_MAX)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        return mask

    def _detecter_centres_ligne(self, image_bgr):
        """Retourne 2 points (devant, derriere) de la ligne, ou (None, None)."""
        try:
            mask = self._masque_rouge(image_bgr)
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
            point_devant = tuple(points[np.argmin(y)])
            point_derriere = tuple(points[np.argmax(y)])

            if abs(point_devant[1] - point_derriere[1]) < 50:
                tries = points[np.argsort(points[:, 1])]
                if len(tries) >= 2:
                    point_devant = tuple(tries[int(len(tries) * 0.25)])
                    point_derriere = tuple(tries[int(len(tries) * 0.75)])

            return point_devant, point_derriere
        except Exception as e:
            print(f"Erreur detection: {e}")
            return None, None

    def _position_ligne(self, image_bgr):
        """Retourne la position x du centre de la ligne rouge, ou None (mode degrade)."""
        mask = self._masque_rouge(image_bgr)
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

    def _bleu_proche(self, image_bgr):
        """Retourne True si une zone bleue suffisante est proche (bas de l'image)."""
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, BLEU_MIN, BLEU_MAX)
        mask[:BLEU_ZONE_BAS, :] = 0
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False
        largest = max(contours, key=cv2.contourArea)
        return cv2.contourArea(largest) > BLEU_AIRE_ARRET

    @staticmethod
    def _calculer_angle(point_devant, point_derriere):
        dx = point_devant[0] - point_derriere[0]
        dy = point_devant[1] - point_derriere[1]
        return math.degrees(math.atan2(dx, -dy))

    # ------------------------------------------------------------------
    # METHODE PRINCIPALE : appelee par le main a chaque tour de boucle
    # ------------------------------------------------------------------
    def analyser(self):
        """
        Capture une image, detecte tout, met a jour le flux web, et renvoie
        un dictionnaire d'infos pour que le main pilote le robot :

          'bleu'            : bool  -> ruban bleu proche (il faut s'arreter)
          'ligne_detectee'  : bool  -> une ligne rouge est visible
          'mode'            : 'complet' | 'degrade' | 'perdu'
          'erreur_position' : int   -> ecart lateral / centre (px), ou None
          'angle'           : float -> orientation de la ligne (deg), ou None
          'image'           : l'image BGR (pour annotation/debug si besoin)
          'centre'          : x du centre de l'image
        """
        image_bgr = self.picam2.capture_array()

        infos = {
            "bleu": False,
            "ligne_detectee": False,
            "mode": "perdu",
            "erreur_position": None,
            "angle": None,
            "image": image_bgr,
            "centre": self.centre_image,
        }

        # 1) Ruban bleu (priorite)
        if self._bleu_proche(image_bgr):
            infos["bleu"] = True
            self._annoter(image_bgr, "STOP (bleu detecte)", (255, 0, 0))
            self.publier(image_bgr)
            return infos

        # 2) Detection complete (position + angle)
        pt_devant, pt_derriere = self._detecter_centres_ligne(image_bgr)
        if pt_devant is not None and pt_derriere is not None:
            infos["ligne_detectee"] = True
            infos["mode"] = "complet"
            infos["erreur_position"] = pt_derriere[0] - self.centre_image
            infos["angle"] = self._calculer_angle(pt_devant, pt_derriere)

            if self.streaming_actif:
                cv2.line(image_bgr, (self.centre_image, 0),
                         (self.centre_image, self.hauteur), (0, 255, 0), 1)
                cv2.line(image_bgr, pt_derriere, pt_devant, (0, 0, 255), 2)
                cv2.circle(image_bgr, pt_devant, 6, (0, 255, 255), -1)
                cv2.circle(image_bgr, pt_derriere, 6, (255, 0, 255), -1)
                cv2.putText(image_bgr,
                            f"Complet - Err:{infos['erreur_position']} Ang:{int(infos['angle'])}",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            self.publier(image_bgr)
            return infos

        # 3) Mode degrade (position seule)
        x_ligne = self._position_ligne(image_bgr)
        if x_ligne is not None:
            infos["ligne_detectee"] = True
            infos["mode"] = "degrade"
            infos["erreur_position"] = x_ligne - self.centre_image

            if self.streaming_actif:
                cv2.line(image_bgr, (self.centre_image, 0),
                         (self.centre_image, self.hauteur), (0, 255, 0), 1)
                cv2.circle(image_bgr, (x_ligne, 400), 8, (0, 165, 255), -1)
                cv2.putText(image_bgr, f"Degrade - Err:{infos['erreur_position']}",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            self.publier(image_bgr)
            return infos

        # 4) Ligne perdue
        self._annoter(image_bgr, "Ligne perdue", (0, 0, 255))
        self.publier(image_bgr)
        return infos

    def _annoter(self, image_bgr, texte, couleur):
        if self.streaming_actif:
            cv2.putText(image_bgr, texte, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, couleur, 2)

    # ------------------------------------------------------------------
    # STREAMING WEB (optionnel, lecture seule)
    # ------------------------------------------------------------------
    def demarrer_streaming(self):
        self.streaming_actif = True
        threading.Thread(target=self._lancer_serveur_web, daemon=True).start()

    def publier(self, image_bgr):
        if not self.streaming_actif:
            return
        success, jpeg = cv2.imencode(".jpg", image_bgr)
        if success:
            with self._verrou:
                self._jpeg = jpeg

    def _lancer_serveur_web(self):
        flux = self

        class StreamingHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/":
                    html = """
                    <html><head><title>Moniteur Robot</title>
                    <style>body{font-family:monospace;text-align:center;background:#1a1a1a;color:#fff;padding:20px}
                    h1{color:#0f0}img{max-width:100%;border:2px solid #444}</style></head>
                    <body><h1>Retour Video</h1><img src="/stream.mjpg" /></body></html>
                    """
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(html)))
                    self.end_headers()
                    self.wfile.write(html.encode("utf-8"))
                elif self.path == "/stream.mjpg":
                    self.send_response(200)
                    self.send_header("Age", 0)
                    self.send_header("Cache-Control", "no-cache, private")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Content-Type",
                                     "multipart/x-mixed-replace; boundary=FRAME")
                    self.end_headers()
                    try:
                        while True:
                            with flux._verrou:
                                jpeg = flux._jpeg
                            if jpeg is None:
                                time.sleep(0.01)
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
                else:
                    self.send_error(404)

            def log_message(self, *args):
                pass

        serveur = HTTPServer(("0.0.0.0", self.port_web), StreamingHandler)
        print(f"Interface video : http://{self._ip_locale()}:{self.port_web}")
        serveur.serve_forever()

    @staticmethod
    def _ip_locale():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    def stop(self):
        self.picam2.stop()