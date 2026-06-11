import RPi.GPIO as GPIO
import CapteurSuiviLigne
import time

previous_time = 0

def delay(ms):
    global previous_time
    current_time = time.time() * 1000
    
    if current_time >= previous_time + ms:
        previous_time = current_time
        return True
    
    return False
        

if __name__ == '__main__':
    try:
        while True:
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("Fin de programme par Ctrl-C")
    finally:
        GPIO.cleanup()  # réinitialise les ports GPIO (ou celle de gpiozero)
        # ou appeler une fonction perso adaptée au robot
        print("Nettoyage final réalisé")
