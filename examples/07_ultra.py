from gpiozero import DistanceSensor
from time import sleep

class CapteurMesureUltrason:
    _broche_echo = 24
    _broche_declencheur = 23

    distance_max = 2.0  # Distance de détection maximale : 2 m.

    def __init__(self):
        self._capteur = DistanceSensor(
            echo=self._broche_echo,
            trigger=self._broche_declencheur,
            max_distance=self.distance_max
        )

    def distance(self):
        return self._capteur.distance * 1000.0  # Unité : mm

if __name__ == "__main__":
    capteur_ultrason = CapteurMesureUltrason()

    while True:
        print("%.0f mm" % capteur_ultrason.distance())
        sleep(0.05)
