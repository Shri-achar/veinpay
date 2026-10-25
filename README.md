# VeinPay

A contactless **palm-image payment prototype** built on a Raspberry Pi 5 as our final-year ECE major project.
A merchant picks an amount, the customer holds a palm over a NoIR camera, the system finds the closest
enrolled palm, and a **simulated** wallet transaction is triggered.

> **Honest status:** this is a palm-*image* matching prototype, not a validated palm-*vein* biometric.
> Our 850 nm reflective setup has not shown a clearly identifiable vein network, and our measured
> genuine-vs-impostor scores still overlap. Authentication and payments are deliberately kept
> disabled during experiments. See [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md).

## What we built

| Area | What it does | Where |
|---|---|---|
| Web dashboard | Flask app: live camera feed, user enrollment, scan/identify, merchant wallet, payment pages | `dashboard/` |
| Camera | Picamera2 capture + MJPEG streaming (NoIR Camera Module 3, autofocus) | `camera/`, `camera_stream.py`, `live_camera.py` |
| Image processing | Grayscale, CLAHE, Gaussian blur, Frangi vesselness, ORB features, Hamming matching | `processing/` |
| Enrollment | Capture ~10 samples per user and store templates | `enrollment/` |
| Database | SQLite: users, wallets, merchants, payment requests, payment processor, migrations | `database/` |
| Hardware | VL53L0X ToF distance sensor, SSD1306 OLED, 850 nm IR LEDs, buzzer | `hardware/`, `sensors/` |
| Notifications | Email receipts (Gmail SMTP via env vars) and voice prompts | `notifications/` |
| Experiments | Algorithm comparison scripts, results, standalone upload-only matcher | `experiments/` |

## Hardware

- Raspberry Pi 5, Raspberry Pi Camera Module 3 **NoIR** (IMX708)
- 2x 850 nm NIR emitters (reflectance geometry)
- VL53L0X time-of-flight sensor (I2C `0x29`), SSD1306 0.96" OLED (I2C `0x3c`)
- MLX90614 temperature sensor was dropped (hardware failure)

## Pipeline (current dashboard)

```
NoIR camera -> crop ROI -> grayscale -> CLAHE -> blur -> Frangi filter
            -> ORB keypoints/descriptors -> BFMatcher (Hamming, cross-check)
            -> score vs each enrolled template -> best candidate
```

Details and a file-by-file map are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Running it (on the Pi)

```bash
pip install -r requirements.txt        # plus: sudo apt install python3-picamera2
export VEINPAY_EMAIL="sender@gmail.com"       # optional, for email receipts
export VEINPAY_APP_PASSWORD="gmail-app-password"
/usr/bin/python3 dashboard/app.py      # serves on port 5000
```

Use the system Python (it has `picamera2`). Only one process can use the camera at a time.

The standalone matcher in `experiments/veinpay_simple_matcher/` needs no camera:
`pip install -r requirements.txt && python app.py` then open `http://127.0.0.1:5055`.

## Privacy

Palm images are biometric data. This repo contains **source code only**: no photos, templates,
databases or audio. `.gitignore` blocks them. Please keep it that way.

## Team

Six-member capstone team at BMS College of Engineering, Bengaluru.
