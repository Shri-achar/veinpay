
"""
VeinPay - Palm Algorithm Comparison

Compare three preprocessing and ORB matching methods:

1. OLD_FRANGI
   - Older vein_test.py processing settings
   - ROI: X 18-72%, Y 18-82%
   - CLAHE clip limit: 3.0
   - Frangi sigmas: 1-5

2. CURRENT_FRANGI
   - Current-style processing configuration
   - Central 70% ROI
   - CLAHE clip limit: 2.0
   - Frangi sigmas: 1-4

3. CLAHE_ORB
   - Central 70% ROI
   - CLAHE without Frangi
   - ORB matching on enhanced palm image

Enrollment:
    Shrinidhi's 10 original left-palm images

Test data:
    6 genuine Shrinidhi left-palm scans
    3 Shrinidhi right-palm scans
    3 different-person left-palm scans

IMPORTANT:
    Experimental matching only.
    Scores are not biometric confidence percentages.
    No authentication or payment is performed.
    Existing VeinPay files are not modified.
"""

from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
from skimage.filters import frangi


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent

ENROLLMENT_DIR = ROOT / "templates/user_23/raw"

CAPTURE_DIR = ROOT / "captured_images"


# ============================================================
# METHODS
# ============================================================

METHODS = [
    "OLD_FRANGI",
    "CURRENT_FRANGI",
    "CLAHE_ORB",
]


# ============================================================
# TEST IMAGES
# ============================================================

TEST_IMAGES = [

    # Shrinidhi - previous genuine LEFT-palm scans
    ("SHRINIDHI_LEFT", "palm_20261015_173036.jpg"),
    ("SHRINIDHI_LEFT", "palm_20261015_173059.jpg"),
    ("SHRINIDHI_LEFT", "palm_20261015_173111.jpg"),

    # Shrinidhi - NEW genuine LEFT-palm scans
    ("SHRINIDHI_LEFT", "palm_20261016_131412.jpg"),
    ("SHRINIDHI_LEFT", "palm_20261016_131428.jpg"),
    ("SHRINIDHI_LEFT", "palm_20261016_131500.jpg"),

    # Shrinidhi - unenrolled RIGHT-palm scans
    ("SHRINIDHI_RIGHT", "palm_20261015_174109.jpg"),
    ("SHRINIDHI_RIGHT", "palm_20261015_174126.jpg"),
    ("SHRINIDHI_RIGHT", "palm_20261015_174146.jpg"),

    # Different person - YOUR LEFT-palm scans
    ("YOUR_LEFT", "palm_20261016_122854.jpg"),
    ("YOUR_LEFT", "palm_20261016_122931.jpg"),
    ("YOUR_LEFT", "palm_20261016_122945.jpg"),
]


NEW_GENUINE_IMAGES = {
    "palm_20261016_131412.jpg",
    "palm_20261016_131428.jpg",
    "palm_20261016_131500.jpg",
}


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess(path, method):
    """
    Apply the preprocessing configuration for one method.

    OLD_FRANGI is based on processing/vein_test.py.

    CURRENT_FRANGI recreates our current-style settings
    for comparison, rather than importing the live pipeline.
    """

    image = cv2.imread(str(path))

    if image is None:
        raise FileNotFoundError(
            f"Unable to load image: {path}"
        )

    height, width = image.shape[:2]

    if method == "OLD_FRANGI":

        x1 = int(width * 0.18)
        x2 = int(width * 0.72)

        y1 = int(height * 0.18)
        y2 = int(height * 0.82)

        clip_limit = 3.0

    elif method in ("CURRENT_FRANGI", "CLAHE_ORB"):

        x1 = int(width * 0.15)
        x2 = int(width * 0.85)

        y1 = int(height * 0.15)
        y2 = int(height * 0.85)

        clip_limit = 2.0

    else:
        raise ValueError(
            f"Unknown method: {method}"
        )

    roi = image[y1:y2, x1:x2]

    if roi.size == 0:
        raise RuntimeError(
            f"Invalid ROI: {path}"
        )

    gray = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2GRAY
    )

    clahe = cv2.createCLAHE(
        clipLimit=clip_limit,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # Surface-feature method; do not apply Frangi.
    if method == "CLAHE_ORB":
        return enhanced

    blurred = cv2.GaussianBlur(
        enhanced,
        (5, 5),
        0
    )

    if method == "OLD_FRANGI":
        sigmas = range(1, 6)
    else:
        sigmas = range(1, 5)

    filtered = frangi(
        blurred,
        sigmas=sigmas,
        black_ridges=True
    )

    filtered = cv2.normalize(
        filtered,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    return filtered.astype(np.uint8)


# ============================================================
# ORB FEATURE EXTRACTION
# ============================================================

def extract_descriptors(image):
    """
    Extract up to 1000 ORB keypoints and their descriptors.
    """

    orb = cv2.ORB_create(
        nfeatures=1000
    )

    keypoints, descriptors = orb.detectAndCompute(
        image,
        None
    )

    return len(keypoints), descriptors


# ============================================================
# ORB FEATURE MATCHING
# ============================================================

def match_descriptors(query, reference):
    """
    Cross-checked Hamming matching.

    Score = 100 * (good matches / total matches)

    Good matches are those with Hamming distance < 50.

    This is NOT biometric recognition confidence.
    """

    if query is None or reference is None:
        return 0.0, 0, 0

    matcher = cv2.BFMatcher(
        cv2.NORM_HAMMING,
        crossCheck=True
    )

    matches = matcher.match(
        query,
        reference
    )

    if not matches:
        return 0.0, 0, 0

    good_matches = [
        match
        for match in matches
        if match.distance < 50
    ]

    score = (
        len(good_matches) / len(matches)
    ) * 100.0

    return (
        float(score),
        len(matches),
        len(good_matches)
    )


# ============================================================
# GROUP SUMMARY
# ============================================================

def print_group_summary(group, scores):

    values = np.asarray(
        scores,
        dtype=np.float32
    )

    print(f"\n{group}")
    print("-" * 45)

    print(
        f"  Number of scans: {len(values)}"
    )

    print(
        f"  Mean Top-3: {np.mean(values):.2f}%"
    )

    print(
        f"  Minimum:    {np.min(values):.2f}%"
    )

    print(
        f"  Maximum:    {np.max(values):.2f}%"
    )


# ============================================================
# TEST ONE METHOD
# ============================================================

def test_method(method, enrollment_paths):

    print("\n" + "=" * 72)
    print("METHOD:", method)
    print("=" * 72)

    start_time = perf_counter()

    reference_data = []

    print("\nPreparing enrollment templates...")

    for path in enrollment_paths:

        processed = preprocess(
            path,
            method
        )

        keypoint_count, descriptors = extract_descriptors(
            processed
        )

        reference_data.append({
            "name": path.name,
            "keypoints": keypoint_count,
            "descriptors": descriptors,
        })

        print(
            f"  {path.name}: "
            f"{keypoint_count} keypoints"
        )

    # Grouped results.
    results = {
        "SHRINIDHI_LEFT": [],
        "SHRINIDHI_RIGHT": [],
        "YOUR_LEFT": [],
    }

    new_genuine_scores = []

    median_match_counts = []

    print("\n" + "-" * 72)
    print("TESTING CAPTURED PALM IMAGES")
    print("-" * 72)

    for group, filename in TEST_IMAGES:

        path = CAPTURE_DIR / filename

        processed = preprocess(
            path,
            method
        )

        query_keypoints, query_descriptors = (
            extract_descriptors(processed)
        )

        scores = []
        match_counts = []
        good_match_counts = []

        for reference in reference_data:

            score, total_matches, good_matches = (
                match_descriptors(
                    query_descriptors,
                    reference["descriptors"]
                )
            )

            scores.append(score)
            match_counts.append(total_matches)
            good_match_counts.append(good_matches)

        score_array = np.asarray(
            scores,
            dtype=np.float32
        )

        ranking = np.argsort(
            score_array
        )[::-1]

        top_indices = ranking[
            :min(3, len(ranking))
        ]

        best_index = int(ranking[0])

        max_score = float(
            score_array[best_index]
        )

        top3_score = float(
            np.mean(
                score_array[top_indices]
            )
        )

        best_template = reference_data[
            best_index
        ]["name"]

        selected_match_counts = [
            match_counts[int(index)]
            for index in top_indices
        ]

        selected_good_counts = [
            good_match_counts[int(index)]
            for index in top_indices
        ]

        median_matches = float(
            np.median(selected_match_counts)
        )

        median_good = float(
            np.median(selected_good_counts)
        )

        median_match_counts.append(
            median_matches
        )

        results[group].append(
            top3_score
        )

        if filename in NEW_GENUINE_IMAGES:
            new_genuine_scores.append(
                top3_score
            )

        print()
        print("-" * 72)
        print(f"Group: {group}")
        print(f"Image: {filename}")
        print("-" * 72)

        if filename in NEW_GENUINE_IMAGES:
            print("*** NEW GENUINE SCAN ***")

        print(
            f"Query keypoints: {query_keypoints}"
        )

        print(
            f"MAX score:       {max_score:.2f}%"
        )

        print(
            f"Top-3 score:     {top3_score:.2f}%"
        )

        print(
            f"Best template:   {best_template}"
        )

        print(
            "Median matches among Top-3:",
            f"{median_matches:.0f}"
        )

        print(
            "Median good matches among Top-3:",
            f"{median_good:.0f}"
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("GROUP SUMMARY -", method)
    print("=" * 72)

    for group, scores in results.items():
        print_group_summary(
            group,
            scores
        )

    genuine_scores = results[
        "SHRINIDHI_LEFT"
    ]

    right_scores = results[
        "SHRINIDHI_RIGHT"
    ]

    other_scores = results[
        "YOUR_LEFT"
    ]

    negative_scores = (
        right_scores + other_scores
    )

    lowest_genuine = min(
        genuine_scores
    )

    highest_right = max(
        right_scores
    )

    highest_other = max(
        other_scores
    )

    highest_negative = max(
        negative_scores
    )

    right_gap = (
        lowest_genuine - highest_right
    )

    different_person_gap = (
        lowest_genuine - highest_other
    )

    overall_gap = (
        lowest_genuine - highest_negative
    )

    elapsed = (
        perf_counter() - start_time
    )

    print("\n" + "=" * 72)
    print("SEPARATION ANALYSIS")
    print("=" * 72)

    print(
        f"Lowest genuine score:       "
        f"{lowest_genuine:.2f}%"
    )

    print(
        f"Highest Shrinidhi right:    "
        f"{highest_right:.2f}%"
    )

    print(
        f"Highest different person:   "
        f"{highest_other:.2f}%"
    )

    print(
        f"Highest negative overall:   "
        f"{highest_negative:.2f}%"
    )

    print(
        f"Left-vs-right gap:          "
        f"{right_gap:+.2f} points"
    )

    print(
        f"Different-person gap:       "
        f"{different_person_gap:+.2f} points"
    )

    print(
        f"Overall separation gap:     "
        f"{overall_gap:+.2f} points"
    )

    if overall_gap > 0:

        print(
            "\nRESULT: No score overlap "
            "within this small test set."
        )

    else:

        print(
            "\nRESULT: Genuine and unenrolled "
            "score ranges overlap."
        )

    print("\n" + "-" * 72)
    print("NEW GENUINE SCANS")
    print("-" * 72)

    for index, score in enumerate(
        new_genuine_scores,
        start=1
    ):

        print(
            f"New scan {index}: "
            f"{score:.2f}%"
        )

    if new_genuine_scores:

        print(
            "Lowest NEW genuine score:",
            f"{min(new_genuine_scores):.2f}%"
        )

    print(
        "\nMedian selected match count:",
        f"{np.median(median_match_counts):.0f}"
    )

    print(
        "Total processing time:",
        f"{elapsed:.2f} seconds"
    )

    return {
        "method": method,
        "genuine_mean": float(
            np.mean(genuine_scores)
        ),
        "right_mean": float(
            np.mean(right_scores)
        ),
        "other_mean": float(
            np.mean(other_scores)
        ),
        "lowest_genuine": float(
            lowest_genuine
        ),
        "highest_negative": float(
            highest_negative
        ),
        "different_person_gap": float(
            different_person_gap
        ),
        "overall_gap": float(
            overall_gap
        ),
        "median_matches": float(
            np.median(median_match_counts)
        ),
        "seconds": float(elapsed),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 72)
    print("VEINPAY - FRESH PALM RECOGNITION COMPARISON")
    print("=" * 72)

    enrollment_paths = sorted(
        ENROLLMENT_DIR.glob("sample_*.jpg")
    )

    if not enrollment_paths:

        raise SystemExit(
            "No enrollment templates found."
        )

    missing_images = [
        filename
        for _, filename in TEST_IMAGES
        if not (CAPTURE_DIR / filename).is_file()
    ]

    if missing_images:

        raise SystemExit(
            "Missing captured images:\n"
            + "\n".join(missing_images)
        )

    print()
    print("Enrolled user: Shrinidhi (User 23)")
    print("Enrollment samples:", len(enrollment_paths))
    print("Total test images:", len(TEST_IMAGES))
    print(
        "New genuine scans:",
        len(NEW_GENUINE_IMAGES)
    )

    summaries = []

    for method in METHODS:

        summary = test_method(
            method,
            enrollment_paths
        )

        summaries.append(
            summary
        )

    # --------------------------------------------------------
    # FINAL COMPARISON TABLE
    # --------------------------------------------------------

    print("\n" + "=" * 90)
    print("FINAL SIDE-BY-SIDE RESULTS")
    print("=" * 90)

    print(
        f"{'Method':<18}"
        f"{'Genuine':>10}"
        f"{'Your Left':>12}"
        f"{'Other Gap':>12}"
        f"{'All Gap':>11}"
        f"{'Matches':>10}"
        f"{'Time':>10}"
    )

    print("-" * 90)

    for item in summaries:

        print(
            f"{item['method']:<18}"
            f"{item['genuine_mean']:>9.2f}%"
            f"{item['other_mean']:>11.2f}%"
            f"{item['different_person_gap']:>12.2f}"
            f"{item['overall_gap']:>11.2f}"
            f"{item['median_matches']:>10.0f}"
            f"{item['seconds']:>9.1f}s"
        )

    print("\n" + "=" * 90)
    print("EXPERIMENT COMPLETED")
    print("=" * 90)

    print(
        "Scores are ORB good-match ratios, "
        "not authentication confidence."
    )

    print(
        "No authentication or payment was performed."
    )

    print(
        "Results from 12 test images do not establish "
        "biometric recognition reliability."
    )


if __name__ == "__main__":
    main()
