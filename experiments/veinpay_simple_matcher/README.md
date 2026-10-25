# VeinPay — Standalone Simple Image Matcher

An upload-based experimental comparison website. It does **not** connect to the camera or alter the existing `VeinPay` Flask dashboard. It does not execute payments or validate biometric identity.

## On Raspberry Pi (recommended: isolated virtual environment)

```bash
cd ~/VeinPay
# Copy the veinpay_simple_matcher directory into this location first
cd veinpay_simple_matcher
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

On the same machine, visit `http://127.0.0.1:5055`. From another laptop via SSH, use VS Code **Ports** → **Forward a Port** → `5055`, then open `http://localhost:5055` in the laptop browser. Avoid exposing this demo service directly on an untrusted hotspot or public internet.

## How it works

1. Upload a reference image, label it, and press **Save reference**.
2. The server converts it to grayscale, applies CLAHE, assigns a unique `VP-...` ID, and saves a PNG in `data/references/`; metadata goes in `data/references.sqlite3`.
3. Upload a test image and press **Compare image**. The same CLAHE preprocessing is applied, ORB descriptors are matched to every reference using cross-checked BF Hamming, and results are ranked.
4. A conservative demonstration heuristic displays `POSSIBLE MATCH`, `NO RELIABLE MATCH`, or `INSUFFICIENT FEATURES`. The user-set threshold is not calibrated, and results are **not biometric identity proof**.

For meaningful tests, use photos that were captured and processed consistently. If you already have fully Frangi-processed reference images, apply the **same** Frangi preprocessing to test images before upload; this standalone app does not run Frangi. Uploading different processing styles will produce misleading scores. Do not interpret the score as confidence.

## Safety / limitations

- No camera integration, no liveness, no payments, no authentication.
- Local development use only; no login, CSRF protection, or production hardening.
- Threshold 40% is a demo setting, **not** a validated value. Prior VeinPay tests showed overlapping scores between enrolled and unenrolled palms.
- If your images are missing consistent corresponding features, this algorithm cannot fix it.
