import os


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "veingate.db"
)

TEMPLATES_DIR = os.path.join(
    BASE_DIR,
    "templates"
)

CAPTURED_IMAGES_DIR = os.path.join(
    BASE_DIR,
    "captured_images"
)

LOGS_DIR = os.path.join(
    BASE_DIR,
    "logs"
)


# ============================================================
# PALM POSITION
# ============================================================

# Final values can be tuned after hardware testing.
# These are our intended operating limits.

MIN_PALM_DISTANCE_CM = 5.0

MAX_PALM_DISTANCE_CM = 10.0


# ============================================================
# CAMERA
# ============================================================

CAMERA_WIDTH = 640

CAMERA_HEIGHT = 480


# ============================================================
# IMAGE PROCESSING
# ============================================================

CLAHE_CLIP_LIMIT = 2.0

CLAHE_TILE_SIZE = (
    8,
    8
)

GAUSSIAN_KERNEL = (
    3,
    3
)

FRANGI_SIGMA_START = 1

FRANGI_SIGMA_END = 5


# ============================================================
# FEATURE EXTRACTION
# ============================================================

ORB_FEATURE_COUNT = 1000

ORB_GOOD_MATCH_DISTANCE = 50


# ============================================================
# BIOMETRIC THRESHOLD
# ============================================================

# IMPORTANT:
# Do NOT set the final threshold until real NIR
# palm images are collected.

AUTHENTICATION_THRESHOLD = None


# ============================================================
# ENROLLMENT
# ============================================================

ENROLLMENT_SAMPLE_COUNT = 10


# ============================================================
# DEFAULT WALLET
# ============================================================

DEFAULT_WALLET_BALANCE = 1000.0


# ============================================================
# FLASK
# ============================================================

FLASK_HOST = "0.0.0.0"

FLASK_PORT = 5000


# ============================================================
# HARDWARE GPIO
# ============================================================

# These will be filled only after final wiring is verified.

IR_LED_GPIO = None

BUZZER_GPIO = None