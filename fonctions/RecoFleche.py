import cv2
import numpy as np

class RecoFleche:
    def __init__(self):
        pass

    def detecter(self, image):
        direction = "Inconnue"

        #Conversion en niveaux de gris
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        #Floutage pour réduire le bruit
        image_blur = cv2.GaussianBlur(image_gray, (5, 5), 0)
        #Détection des contours
        corners = cv2.goodFeaturesToTrack(
            image_blur,
            10,
            qualityLevel=0.01,
            minDistance=10
        )

        if corners is not None:
            corners = corners.astype(int)
            points = corners.reshape(-1, 2)

            for point in points:
                x, y = point
                cv2.circle(image, (x, y), 5, (0, 255, 0), -1)

            point_min_x = points[np.argmin(points[:, 0])]
            point_max_x = points[np.argmax(points[:, 0])]

            xmin = point_min_x[0]
            xmax = point_max_x[0]

            xmoyenne = int((xmin + xmax) / 2)

            cv2.circle(image, tuple(point_min_x), 10, (255, 0, 0), -1)
            cv2.circle(image, tuple(point_max_x), 10, (0, 0, 255), -1)

            cv2.line(image, (xmoyenne, 0), (xmoyenne, image.shape[0]), (255, 255, 0), 2)

            nb_left = 0
            nb_right = 0

            for point in points:
                x= point[0]

                if x < xmoyenne:
                    nb_left += 1

                elif x > xmoyenne:
                    nb_right += 1
            
            if nb_left > nb_right:
                direction = "Gauche"
            elif nb_right > nb_left:
                direction = "Droite"
            else:
                direction = "Inconnue"

            cv2.putText(
                image,
                f"Direction: {direction}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 0),
                2
            )
        
        return image, direction