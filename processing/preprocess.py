import cv2
import numpy as np
from skimage.filters import frangi
import os
import sys


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


from config import (
    CAPTURED_IMAGES_DIR,
    CLAHE_CLIP_LIMIT,
    CLAHE_TILE_SIZE,
    GAUSSIAN_KERNEL,
    FRANGI_SIGMA_START,
    FRANGI_SIGMA_END
)


def crop_center_roi(image):

    height, width = image.shape[:2]

    x1 = int(
        width * 0.15
    )

    x2 = int(
        width * 0.85
    )

    y1 = int(
        height * 0.15
    )

    y2 = int(
        height * 0.85
    )


    roi = image[
        y1:y2,
        x1:x2
    ]


    return roi


def preprocess_palm(
    image_path,
    output_folder=None
):

    image = cv2.imread(
        image_path
    )


    if image is None:

        raise FileNotFoundError(
            f"Palm image not found: {image_path}"
        )


    roi = crop_center_roi(
        image
    )


    gray = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2GRAY
    )


    clahe = cv2.createCLAHE(
        clipLimit=CLAHE_CLIP_LIMIT,
        tileGridSize=CLAHE_TILE_SIZE
    )


    enhanced = clahe.apply(
        gray
    )


    blurred = cv2.GaussianBlur(
        enhanced,
        GAUSSIAN_KERNEL,
        0
    )


    sigma_values = range(
        FRANGI_SIGMA_START,
        FRANGI_SIGMA_END
    )


    veins = frangi(
        blurred,
        sigmas=sigma_values,
        black_ridges=True
    )


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


    results = {

        "original": image,

        "roi": roi,

        "gray": gray,

        "clahe": enhanced,

        "blurred": blurred,

        "frangi": veins
    }


    if output_folder is not None:

        os.makedirs(
            output_folder,
            exist_ok=True
        )


        cv2.imwrite(
            os.path.join(
                output_folder,
                "00_original.png"
            ),
            image
        )


        cv2.imwrite(
            os.path.join(
                output_folder,
                "01_roi.png"
            ),
            roi
        )


        cv2.imwrite(
            os.path.join(
                output_folder,
                "02_gray.png"
            ),
            gray
        )


        cv2.imwrite(
            os.path.join(
                output_folder,
                "03_clahe.png"
            ),
            enhanced
        )


        cv2.imwrite(
            os.path.join(
                output_folder,
                "04_blurred.png"
            ),
            blurred
        )


        cv2.imwrite(
            os.path.join(
                output_folder,
                "05_frangi.png"
            ),
            veins
        )


    return results


if __name__ == "__main__":

    print()

    print(
        "======================================"
    )

    print(
        "       VEINPAY PREPROCESS TEST"
    )

    print(
        "======================================"
    )


    test_image = os.path.join(
        CAPTURED_IMAGES_DIR,
        "test_palm.png"
    )


    output_folder = os.path.join(
        CAPTURED_IMAGES_DIR,
        "processed_test"
    )


    try:

        results = preprocess_palm(
            test_image,
            output_folder
        )


        print()
        print(
            "Palm preprocessing completed."
        )


        print(
            "Output folder:"
        )

        print(
            output_folder
        )


        cv2.imshow(
            "VeinPay - Frangi Result",
            results["frangi"]
        )


        print()

        print(
            "Press any key on the image window to close."
        )


        cv2.waitKey(0)

        cv2.destroyAllWindows()


    except FileNotFoundError as error:

        print()

        print(
            "ERROR:"
        )

        print(
            error
        )