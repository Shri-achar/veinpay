from flask import Flask, request, jsonify
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont


app = Flask(__name__)


# -------------------------------------------------
# OLED INITIALIZATION
# -------------------------------------------------

i2c = busio.I2C(
    board.SCL,
    board.SDA
)

display = adafruit_ssd1306.SSD1306_I2C(
    128,
    64,
    i2c
)

font = ImageFont.load_default()


def show_oled(line1="", line2="", line3=""):

    display.fill(0)
    display.show()

    image = Image.new(
        "1",
        (
            display.width,
            display.height
        )
    )

    draw = ImageDraw.Draw(image)

    draw.text(
        (5, 5),
        line1,
        font=font,
        fill=255
    )

    draw.text(
        (5, 25),
        line2,
        font=font,
        fill=255
    )

    draw.text(
        (5, 45),
        line3,
        font=font,
        fill=255
    )

    display.image(image)
    display.show()


# -------------------------------------------------
# TEST WEB PAGE
# -------------------------------------------------

@app.route("/")
def home():

    return """
<!DOCTYPE html>

<html>

<head>

<title>VeinPay OLED Test</title>

<style>

body {
    background: #0b1118;
    color: white;
    font-family: Arial;
    text-align: center;
    padding-top: 60px;
}

h1 {
    color: #22d3ee;
}

button {
    padding: 15px 25px;
    margin: 10px;
    font-size: 17px;
    border: none;
    border-radius: 10px;
    cursor: pointer;
}

</style>

</head>


<body>

<h1>VeinPay OLED Test</h1>

<p>
Laptop Browser → Raspberry Pi → OLED
</p>


<button onclick="sendMessage('ready')">
PLACE PALM
</button>


<button onclick="sendMessage('scan')">
SCANNING
</button>


<button onclick="sendMessage('success')">
PAYMENT SUCCESS
</button>


<button onclick="sendMessage('failed')">
PAYMENT FAILED
</button>


<script>

async function sendMessage(type) {

    const response =
        await fetch(
            "/oled",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                    "application/json"
                },

                body:
                    JSON.stringify({
                        type: type
                    })
            }
        );


    const result =
        await response.json();


    console.log(result);

}

</script>

</body>

</html>
"""


# -------------------------------------------------
# OLED API
# -------------------------------------------------

@app.route(
    "/oled",
    methods=["POST"]
)
def oled():

    data = request.get_json()

    message_type = data.get(
        "type"
    )


    if message_type == "ready":

        show_oled(
            "VeinPay",
            "PLACE PALM",
            "5 - 10 CM"
        )


    elif message_type == "scan":

        show_oled(
            "VeinPay",
            "SCANNING...",
            "HOLD STILL"
        )


    elif message_type == "success":

        show_oled(
            "PAYMENT",
            "SUCCESSFUL",
            "THANK YOU"
        )


    elif message_type == "failed":

        show_oled(
            "PAYMENT",
            "FAILED",
            "TRY AGAIN"
        )


    return jsonify(
        {
            "success": True,
            "message": message_type
        }
    )


# -------------------------------------------------
# START SERVER
# -------------------------------------------------

if __name__ == "__main__":

    show_oled(
        "VeinPay",
        "WEB TEST",
        "READY"
    )

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False
    )
