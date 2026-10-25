import time
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

i2c = busio.I2C(
    board.SCL,
    board.SDA
)

display = adafruit_ssd1306.SSD1306_I2C(
    128,
    64,
    i2c
)

display.fill(0)
display.show()

image = Image.new(
    "1",
    (display.width, display.height)
)

draw = ImageDraw.Draw(image)

font = ImageFont.load_default()

draw.text(
    (10, 10),
    "VeinPay",
    font=font,
    fill=255
)

draw.text(
    (10, 30),
    "OLED WORKING",
    font=font,
    fill=255
)

display.image(image)
display.show()

print("OLED test displayed")

time.sleep(10)

display.fill(0)
display.show()

print("OLED cleared")
