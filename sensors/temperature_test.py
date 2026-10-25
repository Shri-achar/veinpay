import time
import smbus2

MLX90614_ADDR = 0x5A
AMBIENT_TEMP_REG = 0x06
OBJECT_TEMP_REG = 0x07

bus = smbus2.SMBus(1)

def read_temp(register):
    data = bus.read_word_data(MLX90614_ADDR, register)

    # Swap the returned bytes
    data = ((data & 0xFF) << 8) | (data >> 8)

    temp_kelvin = data * 0.02
    temp_celsius = temp_kelvin - 273.15

    return temp_celsius

print("MLX90614 Temperature Test")
print("-------------------------")

while True:
    try:
        ambient = read_temp(AMBIENT_TEMP_REG)
        obj = read_temp(OBJECT_TEMP_REG)

        print(f"Ambient: {ambient:.2f} °C")
        print(f"Object : {obj:.2f} °C")
        print()

        time.sleep(1)

    except Exception as e:
        print("Sensor read failed:", e)
        break