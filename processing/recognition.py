import cv2
import sqlite3
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
    DATABASE_PATH,
    AUTHENTICATION_THRESHOLD
)

from processing.feature_extract import (
    extract_features,
    match_features
)


def load_template(
    template_path
):

    if not template_path:

        return None


    if not os.path.exists(
        template_path
    ):

        return None


    image = cv2.imread(
        template_path,
        cv2.IMREAD_GRAYSCALE
    )


    return image


def compare_with_template(
    live_image,
    template_image
):

    if (
        live_image is None
        or
        template_image is None
    ):

        return 0.0


    live_keypoints, live_descriptors = (
        extract_features(
            live_image
        )
    )


    template_keypoints, template_descriptors = (
        extract_features(
            template_image
        )
    )


    (
        all_matches,
        good_matches,
        similarity
    ) = match_features(
        live_descriptors,
        template_descriptors
    )


    return similarity


def recognize_user(
    live_image
):

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            user_id,
            name,
            template_path,
            wallet_balance

        FROM users
        """
    )


    users = cursor.fetchall()

    conn.close()


    if len(users) == 0:

        return {
            "matched": False,
            "reason": (
                "No registered users."
            ),
            "best_user": None,
            "best_score": 0.0
        }


    best_user = None

    best_score = 0.0


    for (
        user_id,
        name,
        template_path,
        wallet_balance
    ) in users:


        if (
            not template_path
            or
            template_path
            ==
            "PENDING_REAL_NIR_TEMPLATE"
        ):

            continue


        template_image = load_template(
            template_path
        )


        if template_image is None:

            continue


        similarity = compare_with_template(
            live_image,
            template_image
        )


        if similarity > best_score:

            best_score = similarity


            best_user = {

                "user_id":
                    user_id,

                "name":
                    name,

                "template_path":
                    template_path,

                "wallet_balance":
                    wallet_balance,

                "score":
                    similarity
            }


    if best_user is None:

        return {
            "matched": False,
            "reason": (
                "No valid palm templates available."
            ),
            "best_user": None,
            "best_score": 0.0
        }


    if AUTHENTICATION_THRESHOLD is None:

        return {

            "matched":
                None,

            "reason":
                (
                    "Authentication threshold "
                    "not calibrated yet."
                ),

            "best_user":
                best_user,

            "best_score":
                best_score
        }


    if (
        best_score
        >=
        AUTHENTICATION_THRESHOLD
    ):

        return {

            "matched":
                True,

            "reason":
                "User recognized.",

            "best_user":
                best_user,

            "best_score":
                best_score
        }


    else:

        return {

            "matched":
                False,

            "reason":
                "Palm not recognized.",

            "best_user":
                best_user,

            "best_score":
                best_score
        }


if __name__ == "__main__":

    print()

    print(
        "======================================"
    )

    print(
        "      VEINPAY RECOGNITION MODULE"
    )

    print(
        "======================================"
    )

    print()

    print(
        "Authentication threshold:"
    )

    print(
        AUTHENTICATION_THRESHOLD
    )

    print()


    if (
        AUTHENTICATION_THRESHOLD
        is None
    ):

        print(
            "Correct status:"
        )

        print(
            "Waiting for real NIR data calibration."
        )

    else:

        print(
            "Threshold is configured."
        )