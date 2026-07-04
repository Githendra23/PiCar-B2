from gpiozero import PWMOutputDevice as PWM
from gpiozero import LED
import time

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

    def right_on(self, colour = [1, 1, 1]):
        self.R_R.value = colour[0]
        self.R_G.value = colour[1]
        self.R_B.value = colour[2]

    def left_on(self, colour = [1, 1, 1]):
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
            case 11: # Allumer la LED n°1
                self.led1.on()
            case 21: # Éteindre la LED n°1
                self.led1.off()

            case 12: # Allumer la LED n°2
                self.led2.on()
            case 22: # Éteindre la LED n°2
                self.led2.off()

            case 13: # Allumer la LED n°3
                self.led3.on()
            case 23: # Éteindre la LED n°3
                self.led3.off()

            
            case 14: # Allumer la LED rouge de gauche
                self.L_R.value = 0.0
            case 24: # Éteindre la LED rouge de gauche
                self.L_R.value = 1.0

            case 15: # Allumer la LED verte de gauche
                self.L_G.value = 0.0
            case 25: # Éteindre la LED verte de gauche
                self.L_G.value = 1.0

            case 16: # Allumer la LED bleue de gauche
                self.L_B.value = 0.0
            case 26: # Éteindre la LED bleue de gauche
                self.L_B.value = 1.0

            case 17: # Allumer la LED rouge de droite
                self.R_R.value = 0.0
            case 27: # Éteindre la LED rouge de droite
                self.R_R.value = 1.0  

            case 18: # Allumer la LED verte de gauche
                self.R_G.value = 0.0
            case 28: # Éteindre la LED verte de gauche
                self.R_G.value = 1.0

            case 19: # Allumer la LED bleue de gauche
                self.R_B.value = 0.0
            case 29: # Éteindre la LED bleue de gauche
                self.R_B.value = 1.0

            case default: # Les autres cas
                return "Invalid command"
    
    # Les instructions pour allumer chaque RGB (gauche et droit) individuellement
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
    
    # Clignotant gauche
    def blinkerLeft(self) :
        # On met la lumière en jaune, avec un délai d'extinction et de rallumage de 0.5 seconde
        delay = 0.5

        self.switch(14)
        self.switch(15)
        time.sleep(delay)

        self.switch(24)
        self.switch(25)
        time.sleep(delay)

    # Clignotant droit
    def blinkerRight(self) :
        # On met la lumière en jaune, avec un délai d'extinction et de rallumage de 0.5 seconde
        delay = 0.4
        
        self.switch(17)
        self.switch(18)
        time.sleep(delay)

        self.switch(27)
        self.switch(28)
        time.sleep(delay)

    def off(self) :
        self.switch(24)
        self.switch(25)
        self.switch(26)
        self.switch(27)
        self.switch(28)
        self.switch(29)
    
    # Feux de détresse
    def warnings(self) :
        # On met la lumière en jaune, avec un délai d'extinction et de rallumage de 0.5 seconde
        self.warningsOn()
        time.sleep(0.3)

        self.off()
        time.sleep(0.3)

    def warningsOn(self) :
        self.switch(14)
        self.switch(15)
        self.switch(17)
        self.switch(18)

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
    while True:
        feuxAvant.instruction()
        commande = int(input("Commande : "))
        feuxAvant.switch(commande)
