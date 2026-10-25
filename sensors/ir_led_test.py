from gpiozero import OutputDevice
from time import sleep


IR_PIN = 23


ir_led = OutputDevice(
    IR_PIN,
    active_high=True,
    initial_value=False
)


print("====================================")
print(" VEINGATE IR LED TEST")
print("====================================")

print("IR LED is OFF")
sleep(2)

print("Turning IR LED ON for 10 seconds...")

ir_led.on()

print("GPIO23 ON")

sleep(10)

ir_led.off()

print("GPIO23 OFF")
print("IR LED is OFF")

print("====================================")
print(" TEST COMPLETED")
print("====================================")