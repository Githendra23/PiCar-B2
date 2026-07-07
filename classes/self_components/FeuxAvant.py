import time
from gpiozero import PWMOutputDevice as PWM
from gpiozero import LED


class FeuxAvant():
    # Constructeur
    def __init__(self):
        Left_R = 13
        Left_G = 19
        Left_B = 0

        Right_R = 1
        Right_G = 5
        Right_B = 6

        self.led1 = LED(9)
        self.led2 = LED(25)
        self.led3 = LED(11)

        self.L_R = PWM(pin=Left_R, initial_value=1.0, frequency=2000)
        self.L_G = PWM(pin=Left_G, initial_value=1.0, frequency=2000)
        self.L_B = PWM(pin=Left_B, initial_value=1.0, frequency=2000)

        self.R_R = PWM(pin=Right_R, initial_value=1.0, frequency=2000)
        self.R_G = PWM(pin=Right_G, initial_value=1.0, frequency=2000)
        self.R_B = PWM(pin=Right_B, initial_value=1.0, frequency=2000)

        # Etat non-bloquant : chaque effet a son propre repere de temps + son etat
        self._temps_gauche = 0
        self._temps_droite = 0
        self._temps_warnings = 0
        self._etat_gauche = False
        self._etat_droite = False
        self._etat_warnings = False

    def right_on(self, colour=[1, 1, 1]):
        self.R_R.value = colour[0]
        self.R_G.value = colour[1]
        self.R_B.value = colour[2]

    def left_on(self, colour=[1, 1, 1]):
        self.L_R.value = colour[0]
        self.L_G.value = colour[1]
        self.L_B.value = colour[2]

    def right_off(self):
        self.R_R.value = 0
        self.R_G.value = 0
        self.R_B.value = 0

    def left_off(self):
        self.L_R.value = 0
        self.L_G.value = 0
        self.L_B.value = 0

    def switch(self, commande):
        match commande:
            case 11:
                self.led1.on()
            case 21:
                self.led1.off()
            case 12:
                self.led2.on()
            case 22:
                self.led2.off()
            case 13:
                self.led3.on()
            case 23:
                self.led3.off()
            case 14:
                self.L_R.value = 0.0
            case 24:
                self.L_R.value = 1.0
            case 15:
                self.L_G.value = 0.0
            case 25:
                self.L_G.value = 1.0
            case 16:
                self.L_B.value = 0.0
            case 26:
                self.L_B.value = 1.0
            case 17:
                self.R_R.value = 0.0
            case 27:
                self.R_R.value = 1.0
            case 18:
                self.R_G.value = 0.0
            case 28:
                self.R_G.value = 1.0
            case 19:
                self.R_B.value = 0.0
            case 29:
                self.R_B.value = 1.0
            case default:
                return "Invalid command"

    def instruction(self):
        print("╔═════════╦════════╦════════╗")
        print("║    11   ║   12   ║   13   ║")
        print("║   LED1  ║  LED2  ║  LED3  ║")
        print("╠═════════╬════════╬════════╣")
        print("║    14   ║   15   ║   16   ║")
        print("║   L_R   ║  L_G   ║  L_B   ║")
        print("╠═════════╬════════╬════════╣")
        print("║    17   ║   18   ║   19   ║")
        print("║   R_R   ║  R_G   ║  R_B   ║")
        print("╠═════════╩════════╩════════╣")
        print("║Éteindre : +10             ║")
        print("║Exemple : 24 = éteindre L_R║")
        print("╚═══════════════════════════╝")

    # ------------------------------------------------------------------
    # Clignotant gauche (NON-BLOQUANT).
    # 'maintenant' (ms) est fourni par le main (une seule lecture d'horloge).
    # A chaque fois que le delai est ecoule, on bascule allume <-> eteint.
    # ------------------------------------------------------------------
    def blinker_left(self, maintenant, delai_ms=500):
        if maintenant >= self._temps_gauche + delai_ms:
            self._temps_gauche = maintenant
            self._etat_gauche = not self._etat_gauche
            if self._etat_gauche:
                self.switch(14)
                self.switch(15)
            else:
                self.switch(24)
                self.switch(25)

    # Clignotant droit (NON-BLOQUANT)
    def blinker_right(self, maintenant, delai_ms=500):
        if maintenant >= self._temps_droite + delai_ms:
            self._temps_droite = maintenant
            self._etat_droite = not self._etat_droite
            if self._etat_droite:
                self.switch(17)
                self.switch(18)
            else:
                self.switch(27)
                self.switch(28)

    def off(self):
        self.switch(24)
        self.switch(25)
        self.switch(26)
        self.switch(27)
        self.switch(28)
        self.switch(29)
    
    # Fait des appels de phare
    def appel_de_phares(self) :
        delay = 0.1

        for i in range (3) :
            self.switch(14)
            self.switch(15)
            self.switch(16)
            self.switch(17)
            self.switch(18)
            self.switch(19)
            time.sleep(delay)

            self.switch(24)
            self.switch(25)
            self.switch(26)
            self.switch(27)
            self.switch(28)
            self.switch(29)
            time.sleep(delay)
    

if __name__ == "__main__":
    feuxAvant = FeuxAvant()
    try:
        while True:
            feuxAvant.appel_de_phares()
    except KeyboardInterrupt:
        feuxAvant.off()
        print("Interruption via le clavier.")