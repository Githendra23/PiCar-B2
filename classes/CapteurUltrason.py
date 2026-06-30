from gpiozero import DistanceSensor
from time import sleep

class CapteurUltrason:
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

    def afficher_distance(self) :
        print(f"Distance : {self.distance()}")

    def alert(self, limite) :
        if(self.distance() <= limite) :
            print("Obstacle détecté !!!")


if __name__ == "__main__":
    capteur_ultrason = CapteurUltrason()

    while True:
        print("%.0f mm" % capteur_ultrason.distance())
        sleep(0.01)
