from picamera2 import Picamera2
import cv2
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer
from RecoFleche import RecoFleche
import threading


# Paramètres pour la détection de ligne
LINE_POS_1 = 200  # Position Y de la première ligne de scan
LINE_POS_2 = 300  # Position Y de la deuxième ligne de scan
THRESHOLD = 80    # Seuil de binarisation
LINE_COLOR_SET = 255  # Couleur à détecter (255 pour blanc, 0 pour noir)


def detecter_centres_ligne(image, threshold=THRESHOLD, line_pos_1=LINE_POS_1, line_pos_2=LINE_POS_2, line_color=LINE_COLOR_SET):
    """
    Détecte les centres sur deux lignes horizontales pour une ligne (colorée ou non).
    
    Args:
        image: Image RGB ou BGR
        threshold: Seuil pour la binarisation
        line_pos_1: Position Y de la première ligne de scan
        line_pos_2: Position Y de la deuxième ligne de scan
        line_color: Couleur à détecter (255 pour blanc, 0 pour noir)
    
    Returns:
        tuple: (center1, center2) où chaque centre est (x, y) ou None si non trouvé
    """
    # Convertir en niveaux de gris
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.shape[2] == 3 else image
    
    # Binarisation
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    
    # Nettoyage
    binary = cv2.erode(binary, None, iterations=2)
    binary = cv2.dilate(binary, None, iterations=2)
    
    height, width = binary.shape
    
    # Initialisation des centres
    center1 = None
    center2 = None
    
    try:
        # Ligne 1
        if 0 <= line_pos_1 < height:
            line_pixels = binary[line_pos_1]
            color_indices = np.where(line_pixels == line_color)[0]
            if len(color_indices) > 0:
                # Prendre les extrémités (en évitant les bords de l'image)
                left = color_indices[0] if len(color_indices) > 0 else 0
                right = color_indices[-1] if len(color_indices) > 0 else width - 1
                center1 = (int((left + right) / 2), line_pos_1)
        
        # Ligne 2
        if 0 <= line_pos_2 < height:
            line_pixels = binary[line_pos_2]
            color_indices = np.where(line_pixels == line_color)[0]
            if len(color_indices) > 0:
                left = color_indices[0] if len(color_indices) > 0 else 0
                right = color_indices[-1] if len(color_indices) > 0 else width - 1
                center2 = (int((left + right) / 2), line_pos_2)
                
    except Exception as e:
        print(f"Erreur dans detecter_centres_ligne: {e}")
    
    return center1, center2


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
                
                # Détecter les centres sur la ligne
                center1, center2 = detecter_centres_ligne(image)
                
                # Convertir en BGR pour OpenCV
                image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
                # Dessiner les centres s'ils sont trouvés
                if center1 is not None:
                    cv2.circle(image_bgr, center1, 8, (0, 255, 0), -1)  # Vert pour le premier centre
                    cv2.putText(image_bgr, "C1", (center1[0] + 15, center1[1]), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                if center2 is not None:
                    cv2.circle(image_bgr, center2, 8, (0, 0, 255), -1)  # Rouge pour le deuxième centre
                    cv2.putText(image_bgr, "C2", (center2[0] + 15, center2[1]), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
                # Dessiner les lignes de scan pour visualisation
                cv2.line(image_bgr, (0, LINE_POS_1), (image_bgr.shape[1], LINE_POS_1), (255, 255, 0), 1)
                cv2.line(image_bgr, (0, LINE_POS_2), (image_bgr.shape[1], LINE_POS_2), (255, 255, 0), 1)
                
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
