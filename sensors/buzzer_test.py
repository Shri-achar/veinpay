from gpiozero import Buzzer
from time import sleep

BUZZER_PIN = 18

buzzer = Buzzer(BUZZER_PIN)

print("Long buzzer test starting...")

buzzer.on()

sleep(3)

buzzer.off()

print("Buzzer test completed.")