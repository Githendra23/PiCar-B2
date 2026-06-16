#!/usr/bin/env python3
from gpiozero import TonalBuzzer
from time import sleep

import musics


# Initialize a TonalBuzzer connected to GPIO18 (BCM)
class Buzzer:
    def __init__(self): 
        self.GPIOpin = 18
        self.tonalbuzzer = TonalBuzzer(self.GPIOpin)

    def play(self, tune):
        """
        Play a musical tune using the buzzer.
        :param tune: List of tuples (note, duration), 
        where each tuple represents a note and its duration.
        """
        for note, duration in tune:
            self.tonalbuzzer.play(note)  # Play the note on the buzzer
            sleep(float(duration))  # Delay for the duration of the note
            self.tonalbuzzer.stop()  # Stop playing after the tune is complete

    def bip(self) :
        note = "D4"
        duration = 0.5
        self.tonalbuzzer.play(note)  # Play the note on the buzzer
        sleep(float(duration))  # Delay for the duration of the note
        self.tonalbuzzer.stop()  # Stop playing after the tune is complete
        sleep(float(duration))
    
if __name__ == "__main__":    
    try:
        buzzer = Buzzer()
        buzzer.bip()
        
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt for graceful termination
        print("Fin du programme via le clavier.")