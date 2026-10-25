import cv2
import os
import shutil


# ============================================================
# IMAGE QUALITY
# ============================================================

def calculate_image_quality(
    image_path
):

    image = cv2.imread(
        image_path,
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:

        return 0.0


    # Sharp images produce a larger
    # Laplacian variance value.
    score = cv2.Laplacian(
        image,
        cv2.CV_64F
    ).var()

    return float(score)


# ============================================================
# SELECT BEST TEMPLATES
# ============================================================

def select_best_templates(
    source_directory,
    selected_directory,
    max_templates=3
):

    if not os.path.isdir(
        source_directory
    ):

        return []


    os.makedirs(
        selected_directory,
        exist_ok=True
    )


    candidates = []


    for filename in os.listdir(
        source_directory
    ):

        if not filename.lower().endswith(
            (
                ".jpg",
                ".jpeg",
                ".png"
            )
        ):
            continue


        path = os.path.join(
            source_directory,
            filename
        )


        quality = calculate_image_quality(
            path
        )


        candidates.append(
            (
                quality,
                path,
                filename
            )
        )


    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )


    selected = candidates[
        :max_templates
    ]


    # Clear old selected images
    for filename in os.listdir(
        selected_directory
    ):

        path = os.path.join(
            selected_directory,
            filename
        )

        if os.path.isfile(path):

            os.remove(path)


    results = []


    for quality, source_path, filename in selected:

        destination = os.path.join(
            selected_directory,
            filename
        )

        shutil.copy2(
            source_path,
            destination
        )

        results.append(
            {
                "filename": filename,
                "path": destination,
                "quality_score": quality
            }
        )


    return results


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "VeinPay template_selector module loaded successfully."
    )