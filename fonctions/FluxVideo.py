from picamera2 import Picamera2
import cv2
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer
from RecoFleche import RecoFleche
import threading


# Paramètres pour la détection de ligne au sol (couleur rouge par défaut)
COULEUR_LIGNE_MIN = (0, 100, 100)    # HSV min pour le rouge
COULEUR_LIGNE_MAX = (10, 255, 255)   # HSV max pour le rouge
MIN_CONTOUR_AREA = 500  # Surface minimale pour considérer un contour comme valide


def detecter_centres_ligne_au_sol(image, couleur_min=COULEUR_LIGNE_MIN, couleur_max=COULEUR_LIGNE_MAX):
    """
    Détecte une ligne colorée au sol et retourne 2 points espacés verticalement.
    
    Args:
        image: Image RGB
        couleur_min: Plage HSV minimale pour la couleur de la ligne
        couleur_max: Plage HSV maximale pour la couleur de la ligne
    
    Returns:
        tuple: (point_devant, point_derriere) où chaque point est (x, y) ou None
    """
    try:
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        mask = cv2.inRange(hsv, couleur_min, couleur_max)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
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
        min_y_idx = np.argmin(y_coords)
        max_y_idx = np.argmax(y_coords)
        
        point_devant = tuple(points[min_y_idx])
        point_derriere = tuple(points[max_y_idx])
        
        if abs(point_devant[1] - point_derriere[1]) < 50:
            sorted_points = points[np.argsort(points[:, 1])]
            if len(sorted_points) >= 2:
                point_devant = tuple(sorted_points[int(len(sorted_points) * 0.25)])
                point_derriere = tuple(sorted_points[int(len(sorted_points) * 0.75)])
        
        return point_devant, point_derriere
        
    except Exception as e:
        print(f"Erreur dans detecter_centres_ligne_au_sol: {e}")
        return None, None


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
        self.send_header(
            "Content-Type",
            "multipart/x-mixed-replace; boundary=FRAME"
        )
        self.end_headers()

        try:
            while True:
                image = picam2.capture_array()
                
                # Détecter les deux points sur la ligne au sol
                point_devant, point_derriere = detecter_centres_ligne_au_sol(image)
                
                # Convertir en BGR pour OpenCV
                image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
                # Dessiner les points s'ils sont trouvés
                if point_devant is not None:
                    cv2.circle(image_bgr, point_devant, 8, (0, 255, 0), -1)
                    cv2.putText(image_bgr, "P1", (point_devant[0] + 15, point_devant[1]), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                if point_derriere is not None:
                    cv2.circle(image_bgr, point_derriere, 8, (0, 0, 255), -1)
                    cv2.putText(image_bgr, "P2", (point_derriere[0] + 15, point_derriere[1]), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
                # Dessiner la ligne entre les deux points pour visualisation
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
    print(f"Serveur lancé sur le port {port}")
    server.serve_forever()


if __name__ == "__main__":
    try:
        serveur = HTTPServer(("0.0.0.0", 8000), StreamingHandler)
        raw_serveur = HTTPServer(("0.0.0.0", 8001), SecondStreamingHandler)

        print("Serveurs lancés.")
        print("Flux avec détection de flèches : http://10.101.2.116:8000")
        print("Flux avec centres de ligne : http://10.101.2.116:8001")

        # threads séparés
        threading.Thread(target=run_server, args=(serveur, 8000), daemon=True).start()
        threading.Thread(target=run_server, args=(raw_serveur, 8001), daemon=True).start()

        
        while True:
            pass

    except KeyboardInterrupt:
        print("Arrêt des serveurs")

    finally:
        picam2.stop()
