import cv2
import numpy as np
from skimage.filters import frangi
import os

# --------------------------------------------------
# IMAGE PATH
# --------------------------------------------------

IMAGE_PATH = (
    "/home/pi/VeinPay/"
    "captured_images/"
    "palm_20260909_144454.jpg"
)

OUTPUT_DIR = "/home/pi/VeinPay/vein_test_results"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------
# LOAD IMAGE
# --------------------------------------------------

img = cv2.imread(IMAGE_PATH)

if img is None:
    print("ERROR: Image not found")
    print(IMAGE_PATH)
    exit()

print("Image loaded successfully")
print("Image size:", img.shape)

# --------------------------------------------------
# PALM ROI
# --------------------------------------------------

h, w = img.shape[:2]

# Central palm crop
x1 = int(w * 0.18)
x2 = int(w * 0.72)

y1 = int(h * 0.18)
y2 = int(h * 0.82)

roi = img[y1:y2, x1:x2]

cv2.imwrite(
    os.path.join(
        OUTPUT_DIR,
        "1_original_roi.jpg"
    ),
    roi
)

# --------------------------------------------------
# GRAYSCALE
# --------------------------------------------------

gray = cv2.cvtColor(
    roi,
    cv2.COLOR_BGR2GRAY
)

cv2.imwrite(
    os.path.join(
        OUTPUT_DIR,
        "2_gray_roi.jpg"
    ),
    gray
)

# --------------------------------------------------
# CLAHE CONTRAST ENHANCEMENT
# --------------------------------------------------

clahe = cv2.createCLAHE(
    clipLimit=3.0,
    tileGridSize=(8, 8)
)

enhanced = clahe.apply(gray)

cv2.imwrite(
    os.path.join(
        OUTPUT_DIR,
        "3_enhanced_roi.jpg"
    ),
    enhanced
)

# --------------------------------------------------
# NOISE REDUCTION
# --------------------------------------------------

blurred = cv2.GaussianBlur(
    enhanced,
    (5, 5),
    0
)

# --------------------------------------------------
# FRANGI VEIN ENHANCEMENT
# --------------------------------------------------

print("Applying Frangi filter...")

veins = frangi(
    blurred,
    sigmas=range(1, 6),
    black_ridges=True
)

# --------------------------------------------------
# NORMALIZE
# --------------------------------------------------

veins = cv2.normalize(
    veins,
    None,
    0,
    255,
    cv2.NORM_MINMAX
)

veins = veins.astype(
    np.uint8
)

cv2.imwrite(
    os.path.join(
        OUTPUT_DIR,
        "4_vein_result.jpg"
    ),
    veins
)

# --------------------------------------------------
# THRESHOLDED VEIN MAP
# --------------------------------------------------

_, vein_binary = cv2.threshold(
    veins,
    35,
    255,
    cv2.THRESH_BINARY
)

cv2.imwrite(
    os.path.join(
        OUTPUT_DIR,
        "5_vein_binary.jpg"
    ),
    vein_binary
)

# --------------------------------------------------
# FINISH
# --------------------------------------------------

print()
print("====================================")
print(" VEIN PROCESSING COMPLETED")
print("====================================")
print()
print("Input image:")
print(IMAGE_PATH)
print()
print("Results saved in:")
print(OUTPUT_DIR)
print()
print("Generated:")
print("1_original_roi.jpg")
print("2_gray_roi.jpg")
print("3_enhanced_roi.jpg")
print("4_vein_result.jpg")
print("5_vein_binary.jpg")