# Architecture

## Request flow: Scan / Identify

1. Browser opens `/scan` (`dashboard/templates/scan.html`) and shows `/video_feed`.
2. Scan API in `dashboard/app.py` grabs a frame from the camera worker.
3. `processing/scan_controller.py` coordinates the scan (distance gating via ToF, OLED feedback).
4. `processing/preprocess.py` -> grayscale, CLAHE, blur, Frangi.
5. `processing/feature_extract.py` -> ORB descriptors + Hamming matching.
6. `processing/recognition.py` / `template_selector.py` compare against enrolled templates in SQLite.
7. Result returned as a *candidate* with a score. Payment stays unauthorized unless explicitly enabled.

## Enrollment flow

`/enroll` page -> capture ~10 samples -> `enrollment/enroll.py` stores raw samples and user record
(`database/database.py`) -> wallet created with a default balance (`config.py`).

## File map

| File / folder | Purpose |
|---|---|
| `main.py` | Early CLI entry point (ToF-gated flow) |
| `config.py` | Paths, camera size, CLAHE/Frangi/ORB parameters, Flask host/port |
| `dashboard/app.py` | The main Flask app (routes: `/`, `/enroll`, `/scan`, `/payment`, `/merchant-wallet`, `/video_feed`, `/api/status`, ...) |
| `camera_stream.py`, `live_camera.py`, `camera/` | Picamera2 capture and streaming tests |
| `processing/preprocess.py` | CLAHE + Frangi pipeline |
| `processing/feature_extract.py`, `matcher.py` | ORB extraction and matching |
| `processing/recognition.py` | Identify a probe against DB templates |
| `processing/vein_test.py` | Original vein-visibility experiment |
| `database/` | SQLite schema, migrations, payments, merchants, payment requests |
| `hardware/controller.py` | OLED + ToF controller class |
| `sensors/` | One small test script per sensor |
| `notifications/` | Email (env-var credentials) and voice alerts |
| `experiments/` | Comparison scripts, results log, standalone simple matcher |

Paths in a few scripts (e.g. `/home/pi/VeinPay`) are placeholders from the Pi; adjust for your setup.
