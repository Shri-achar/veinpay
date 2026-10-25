from flask import Flask, Response, render_template_string, jsonify
from picamera2 import Picamera2
from libcamera import controls
import cv2
import time
import os
from datetime import datetime

app = Flask(__name__)

# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = "/home/pi/VeinPay"
CAPTURE_DIR = os.path.join(BASE_DIR, "captured_images")

os.makedirs(CAPTURE_DIR, exist_ok=True)

# --------------------------------------------------
# CAMERA SETUP
# --------------------------------------------------

picam2 = Picamera2()

camera_config = picam2.create_video_configuration(
    main={
        "size": (1280, 720),
        "format": "RGB888"
    }
)

picam2.configure(camera_config)
picam2.start()

time.sleep(1)

# --------------------------------------------------
# AUTOFOCUS
# --------------------------------------------------

try:
    picam2.set_controls({
        "AfMode": controls.AfModeEnum.Continuous,
        "AfSpeed": controls.AfSpeedEnum.Fast
    })

    print("Continuous autofocus enabled")

except Exception as e:
    print("Autofocus control error:")
    print(e)

# --------------------------------------------------
# WEB PAGE
# --------------------------------------------------

HTML = """
<!DOCTYPE html>
<html>

<head>

    <title>VeinPay Camera</title>

    <style>

        body {
            margin: 0;
            background: #111827;
            color: white;
            font-family: Arial, sans-serif;
            text-align: center;
        }

        h1 {
            margin-top: 30px;
            margin-bottom: 5px;
            font-size: 42px;
        }

        .subtitle {
            color: #b9c2d0;
            font-size: 20px;
        }

        .camera-box {
            margin: 30px auto;
            width: 92%;
            max-width: 1100px;

            background: #1f2937;

            padding: 20px;
            border-radius: 20px;
        }

        .camera-view img {
            width: 100%;
            border-radius: 15px;
            display: block;
        }

        .status {
            margin-top: 20px;
            font-size: 28px;
            font-weight: bold;
        }

        .distance {
            margin-top: 8px;
            color: #b9c2d0;
            font-size: 18px;
        }

        .capture-button {
            margin-top: 25px;
            padding: 15px 35px;

            border: none;
            border-radius: 10px;

            font-size: 20px;
            font-weight: bold;

            cursor: pointer;

            background: white;
            color: #111827;
        }

        .capture-button:hover {
            opacity: 0.9;
        }

        #message {
            margin-top: 18px;
            font-size: 18px;
            min-height: 24px;
        }

    </style>

</head>


<body>

<h1>VeinPay</h1>

<div class="subtitle">
    Pay with your palm.
</div>


<div class="camera-box">

    <div class="camera-view">

        <img src="/video_feed">

    </div>


    <div class="status">
        PLACE PALM 5–10 CM FROM CAMERA
    </div>


    <div class="distance">
        Keep palm flat and steady
    </div>


    <button
        class="capture-button"
        onclick="capturePalm()"
    >
        CAPTURE PALM
    </button>


    <div id="message"></div>

</div>


<script>

async function capturePalm() {

    const message = document.getElementById("message");

    message.innerHTML = "Capturing...";

    try {

        const response = await fetch(
            "/capture",
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (data.success) {

            message.innerHTML =
                "Captured successfully: " +
                data.filename;

        } else {

            message.innerHTML =
                "Capture failed: " +
                data.error;

        }

    } catch (error) {

        message.innerHTML =
            "Capture error";

        console.log(error);

    }

}

</script>


</body>

</html>
"""

# --------------------------------------------------
# VIDEO STREAM
# --------------------------------------------------

def generate_frames():

    while True:

        frame = picam2.capture_array()

        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_RGB2BGR
        )

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                90
            ]
        )

        if not success:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )

# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def index():

    return render_template_string(
        HTML
    )

# --------------------------------------------------
# VIDEO FEED
# --------------------------------------------------

@app.route("/video_feed")
def video_feed():

    return Response(
        generate_frames(),
        mimetype=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        )
    )

# --------------------------------------------------
# CAPTURE IMAGE
# --------------------------------------------------

@app.route("/capture", methods=["POST"])
def capture():

    try:

        # Allow autofocus to settle
        time.sleep(0.3)

        frame = picam2.capture_array()

        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_RGB2BGR
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        filename = (
            f"palm_{timestamp}.jpg"
        )

        filepath = os.path.join(
            CAPTURE_DIR,
            filename
        )

        success = cv2.imwrite(
            filepath,
            frame
        )

        if not success:

            return jsonify({
                "success": False,
                "error": "Could not save image"
            })

        print()
        print("Palm captured:")
        print(filepath)

        return jsonify({
            "success": True,
            "filename": filename,
            "filepath": filepath
        })

    except Exception as e:

        print("Capture error:")
        print(e)

        return jsonify({
            "success": False,
            "error": str(e)
        })

# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":

    print()
    print("====================================")
    print(" VEINPAY CAMERA")
    print("====================================")
    print()
    print("Resolution      : 1280 x 720")
    print("Autofocus       : Continuous")
    print("Palm distance   : 5 - 10 cm")
    print("Capture folder  :", CAPTURE_DIR)
    print()
    print("Open browser:")
    print("http://<PI_IP>:5000")
    print()
    print("Press CTRL+C to stop")
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )