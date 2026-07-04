import cv2
import numpy as np


class RecoFleche:
    def __init__(self):
        # Aire minimale du contour pour considérer qu'il y a une flèche
        self.aire_min = 3000

        # Zone de détection : on ignore les bords de l'image
        self.marge_x = 20
        self.marge_y = 20

    def detecter(self, image):

        direction = "Inconnue"

        hauteur, largeur = image.shape[:2]

        #Définir une zone utile
        x1 = self.marge_x
        y1 = self.marge_y
        x2 = largeur - self.marge_x
        y2 = hauteur - self.marge_y

        zone = image[y1:y2, x1:x2]

        # Dessin de la zone analysée
        cv2.rectangle(image, (x1, y1), (x2, y2), (255, 255, 0), 2)

        # Conversion en niveaux de gris
        gray = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)

        # Flou pour réduire le bruit
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Seuillage
        # On suppose que la flèche est sombre sur un fond plus clair.
        _, mask = cv2.threshold(
            blur,
            80,
            255,
            cv2.THRESH_BINARY_INV
        )

        # Nettoyage du masque
        kernel = np.ones((5, 5), np.uint8)

        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Recherche des contours
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if len(contours) == 0:
            self._afficher_direction(image, direction)
            return image, direction

        # Garder le plus gros contour
        contour = max(contours, key=cv2.contourArea)
        aire = cv2.contourArea(contour)

        if aire < self.aire_min:
            self._afficher_direction(image, direction)
            return image, direction

        # Approximation du contour
        perimetre = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.03 * perimetre, True)

        # Replacer le contour dans les coordonnées de l'image complète
        contour_global = contour + np.array([[[x1, y1]]])
        approx_global = approx + np.array([[[x1, y1]]])

        cv2.drawContours(image, [contour_global], -1, (0, 255, 0), 2)
        cv2.drawContours(image, [approx_global], -1, (0, 0, 255), 3)

        # Calcul de l'orientation
        points = contour.reshape(-1, 2)

        x_min = np.min(points[:, 0])
        x_max = np.max(points[:, 0])

        # Centre de masse du contour
        moments = cv2.moments(contour)

        if moments["m00"] == 0:
            self._afficher_direction(image, direction)
            return image, direction

        centre_x = int(moments["m10"] / moments["m00"])

        distance_gauche = centre_x - x_min
        distance_droite = x_max - centre_x

        # Pour une flèche vers la droite :
        # la pointe est à droite, donc x_max est plus éloigné du centre de masse.
        if distance_droite > distance_gauche:
            direction = "Gauche"
        elif distance_gauche > distance_droite:
            direction = "Droite"
        else:
            direction = "Inconnue"

        # Replacer les points dans l'image globale
        centre_x_global = centre_x + x1
        x_min_global = x_min + x1
        x_max_global = x_max + x1

        cv2.line(
            image,
            (centre_x_global, y1),
            (centre_x_global, y2),
            (255, 0, 255),
            2
        )

        cv2.circle(
            image,
            (x_min_global, y1 + 30),
            8,
            (255, 0, 0),
            -1
        )

        cv2.circle(
            image,
            (x_max_global, y1 + 30),
            8,
            (0, 0, 255),
            -1
        )

        self._afficher_direction(image, direction)

        return image, direction

    def _afficher_direction(self, image, direction):
        cv2.putText(
            image,
            f"Direction : {direction}",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

