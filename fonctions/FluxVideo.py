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
from Tourelle import Tourelle
from LedHAT import LedHAT

# Plages de detection du rouge en HSV
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

# Parametres de pilotage
CENTRE_IMAGE = 320          
ZONE_MORTE = 40             
GAIN_POSITION = 0.15        
GAIN_ANGLE = 0.40           
SENS_SERVO = 1              
VITESSE = 30                

# Gestion du streaming et de l'etat partage
streaming_actif = False
etat_partage = {"jpeg": None}
verrou = threading.Lock()


def obtenir_ip_locale():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # créé AVANT le try
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def detecter_centres_ligne_au_sol(image_bgr):
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


def position_ligne_rouge(image_bgr):
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


def calculer_angle(point_devant, point_derriere):
    dx = point_devant[0] - point_derriere[0]
    dy = point_devant[1] - point_derriere[1]   
    angle = math.degrees(math.atan2(dx, -dy))
    return angle


picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "BGR888"}
)
picam2.configure(config)
picam2.start()


class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            html = """
            <html>
                <head>
                    <title>Moniteur de Trajectoire Robot</title>
                    <style>
                        body { font-family: monospace; text-align: center; background: #1a1a1a; color: #ffffff; margin: 0; padding: 20px; }
                        h1 { color: #00ff00; margin-bottom: 10px; }
                        .container { display: inline-block; background: #2a2a2a; padding: 15px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
                        img { max-width: 100%; height: auto; border: 2px solid #444; display: block; }
                        .info { margin-top: 10px; font-size: 14px; color: #aaa; }
                    </style>
                </head>
                <body>
                    <h1>Retour Video & Télémétrie</h1>
                    <div class="container">
                        <img src="/stream.mjpg" />
                        <div class="info">Résolution: 640x480 | Format: BGR888 Natif</div>
                    </div>
                </body>
            </html>
            """
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        elif self.path == "/stream.mjpg":
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


def lancer_serveur_web():
    serveur = HTTPServer(("0.0.0.0", 8000), StreamingHandler)
    print(f"Interface d'observation disponible a l'adresse : http://{obtenir_ip_locale()}:8000")
    serveur.serve_forever()


def demarrer_streaming():
    """Active le flag de capture et initialise le serveur HTTP dans un thread separe."""
    global streaming_actif
    streaming_actif = True
    threading.Thread(target=lancer_serveur_web, daemon=True).start()


def publier(image_bgr):
    """Effectue l'encodage JPEG uniquement si le streaming a ete explicitement active."""
    if not streaming_actif:
        return
        
    success, jpeg = cv2.imencode(".jpg", image_bgr)
    if success:
        with verrou:
            etat_partage["jpeg"] = jpeg


if __name__ == "__main__":
    # =========================================================================
    # CONFIGURATION DU STREAMING
    # Pour desactiver le streaming et alleger le CPU, commentez la ligne ci-dessous.
    # =========================================================================
    demarrer_streaming()
    
    moteur = Moteur()
    direction = Direction()
    tourelle = Tourelle()
    led = LedHAT()

    led.all_off()

    tourelle.reset()
    tourelle.turn_y_axis(50)

    ligne_deja_detectee = False

    try:
        while True:
            image_bgr = cv2.cvtColor(picam2.capture_array(), cv2.COLOR_RGB2BGR)

            # 1) PRIORITE CRITIQUE : detection du ruban bleu
            if bleu_proche(image_bgr):
                moteur.stop()
                direction.reset()
                if streaming_actif:
                    cv2.putText(image_bgr, "STOP (bleu detecte)", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                publier(image_bgr)
                print("Ruban bleu détecté -> Arrêt immédiat de la séquence")
                break

            # 2) Analyse de la ligne rouge
            pt_devant, pt_derriere = detecter_centres_ligne_au_sol(image_bgr)

            if pt_devant is not None and pt_derriere is not None:
                ligne_deja_detectee = True

                erreur_position = pt_derriere[0] - CENTRE_IMAGE
                angle_ligne = calculer_angle(pt_devant, pt_derriere)

                if abs(erreur_position) < ZONE_MORTE and abs(angle_ligne) < 5:
                    angle_cible = direction.getAngleCenter()
                else:
                    correction = (erreur_position * GAIN_POSITION) + (angle_ligne * GAIN_ANGLE)
                    angle_cible = direction.getAngleCenter() - SENS_SERVO * correction
                    angle_cible = max(direction.getAngleMin(),
                                      min(direction.getAngleMax(), angle_cible))

                direction.turn(int(angle_cible))
                moteur.drive(VITESSE)

                if streaming_actif:
                    cv2.line(image_bgr, (CENTRE_IMAGE, 0), (CENTRE_IMAGE, 480), (0, 255, 0), 1)
                    cv2.line(image_bgr, pt_derriere, pt_devant, (0, 0, 255), 2)
                    cv2.circle(image_bgr, pt_devant, 6, (0, 255, 255), -1)   
                    cv2.circle(image_bgr, pt_derriere, 6, (255, 0, 255), -1) 
                    cv2.putText(image_bgr, f"Nominal - Err: {erreur_position} Ang: {int(angle_ligne)}deg",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            else:
                # 3) STRATEGIE DE REPLI NIVEAU 1 : Mode degrade
                x_ligne = position_ligne_rouge(image_bgr)

                if x_ligne is not None:
                    ligne_deja_detectee = True
                    erreur_position = x_ligne - CENTRE_IMAGE

                    if abs(erreur_position) < ZONE_MORTE:
                        angle_cible = direction.getAngleCenter()
                    else:
                        angle_cible = direction.getAngleCenter() - SENS_SERVO * (erreur_position * GAIN_POSITION)
                        angle_cible = max(direction.getAngleMin(),
                                          min(direction.getAngleMax(), angle_cible))

                    direction.turn(int(angle_cible))
                    moteur.drive(VITESSE)

                    if streaming_actif:
                        cv2.line(image_bgr, (CENTRE_IMAGE, 0), (CENTRE_IMAGE, 480), (0, 255, 0), 1)
                        cv2.circle(image_bgr, (x_ligne, 400), 8, (0, 165, 255), -1)
                        cv2.putText(image_bgr, f"Degrade - Err: {erreur_position}",
                                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

                else:
                    # 4) STRATEGIE DE REPLI NIVEAU 2 : Perte totale de contact visuel
                    if ligne_deja_detectee:
                        angle_recherche = direction.getAngleCenter()  
                        direction.turn(int(angle_recherche))
                        moteur.reverse(VITESSE)

                        if streaming_actif:
                            cv2.putText(image_bgr, "PERTE LIGNE : RECUL DROIT", (10, 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 127, 255), 2)
                        print("Alerte : Ligne perdue. Manœuvre de recherche automatique (Recul en ligne droite).")
                    else:
                        moteur.stop()
                        if streaming_actif:
                            cv2.putText(image_bgr, "En attente du repere rouge initial", (10, 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            publier(image_bgr)

    except KeyboardInterrupt:
        print("Arret manuel")
    finally:
        moteur.destroy()
        direction.reset()
        picam2.stop()