import time
from statistics import median

from Moteur import Moteur
from Direction import Direction
from Tourelle import Tourelle

class NavigationLabyrinthe:
    def __init__(self):
        # Propulsion
        self.moteur = Moteur()

        # Direction des roues avant
        self.direction = Direction()

        # Tourelle = servo + capteur ultrason
        self.tourelle = Tourelle()

        # Angles de la tête
        self.ANGLE_TETE_CENTRE=88
        self.ANGLE_TETE_GAUCHE=120
        self.ANGLE_TETE_DROITE=65
        self.ANGLE_TETE_VERTICAL=90

        # Angles des roues
        self.ANGLE_ROUES_CENTRE=90
        self.ANGLE_ROUES_GAUCHE=120
        self.ANGLE_ROUES_DROITE=60

        # Distances en mm
        self.DISTANCE_STOP=200
        self.DISTANCE_LIBRE=350

        # Réglages de sensibilité
        self.NB_MESURES_DISTANCE=5
        self.PAUSE_ENTRE_MESURES=0.04
        self.TEMPS_STABILISATION_SERVO=0.6

        # Vitesses moteur
        self.VITESSE_AVANCE=28
        self.VITESSE_MANOEUVRE=25

        self.initialiser_position()

    def initialiser_position(self):
        """
        POSITION DE DEPART PROPRE :
        roues droites
        tête centrée
        servo vertical centré
        """

        self.moteur.stop()
        self.direction.reset()

        self.tourelle.turn_x_axis(self.ANGLE_TETE_CENTRE)
        self.tourelle.turn_y_axis(self.ANGLE_TETE_VERTICAL)

        time.sleep(0.5)

    def lire_distance_stable(self):
        """
        Lit plusieurs distances et garde la médianne. Evite qu'un valeure parasite décide à la place du robot.
        """

        mesures=[]

        for _ in range(self.NB_MESURES_DISTANCE):
            distance = self.tourelle.getDistance()

            if distance is not None and 20 <= distance <= 2000:
                mesures.append(distance)

            time.sleep(self.PAUSE_ENTRE_MESURES)

        if len(mesures) == 0:
            return 2000
        
        return median(mesures)
    
    def regarder_angle(self, angle):
        """
        Tourne la tête vers un angle donné, attend que le servo soit stable, puis mesure la distance.
        """

        self.tourelle.turn_x_axis(angle)
        time.sleep(self.TEMPS_STABILISATION_SERVO)

        return self.lire_distance_stable()
    
    def scanner_directions(self):

        distances = {}

        distances["gauche"] = self.regarder_angle(self.ANGLE_TETE_GAUCHE)
        distances["centre"] = self.regarder_angle(self.ANGLE_TETE_CENTRE)
        distances["droite"] = self.regarder_angle(self.ANGLE_TETE_DROITE)

        self.tourelle.turn_x_axis(self.ANGLE_TETE_CENTRE)
        time.sleep(0.2)

        return distances
    
    def choisir_direction(self, distances):
        """
        Choisit la direction la plus logique à partir des distances.
        """

        if distances["centre"] >= self.DISTANCE_LIBRE:
            return "centre"
        
        meilleure_direction = max(distances, key=distances.get)

        if distances[meilleure_direction] < self.DISTANCE_STOP:
            return "bloque"
        
        return meilleure_direction
    
    def afficher_scan(self, distances, choix):
        print("----- SCAN LABYRINTHE -----")
        print(f"Gauche : {distances['gauche']:.0f} mm")
        print(f"Centre : {distances['centre']:.0f} mm")
        print(f"Droite : {distances['droite']:.0f} mm")
        print(f"Choix  : {choix}")
        print("---------------------------")

    def arret_propre(self):
            """
            Arrêt propre du robot.
            """

            self.moteur.stop()
            self.direction.reset()
            self.tourelle.reset()
            self.moteur.destroy()