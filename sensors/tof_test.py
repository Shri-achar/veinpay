import time
import board
import busio
import adafruit_vl53l0x


i2c = busio.I2C(
    board.SCL,
    board.SDA
)

sensor = adafruit_vl53l0x.VL53L0X(
    i2c
)


print("VL53L0X started")
print("Press Ctrl+C to stop")


try:

    while True:

        distance_mm = sensor.range

        distance_cm = distance_mm / 10.0

        print(
            f"Distance: {distance_cm:.1f} cm"
        )

        time.sleep(
            0.5
        )


except KeyboardInterrupt:

    print(
        "\nStopped"
    )
