import cv2
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
    ORB_FEATURE_COUNT,
    ORB_GOOD_MATCH_DISTANCE
)


def extract_features(image):

    if image is None:

        raise ValueError(
            "Input image is empty."
        )


    if len(image.shape) == 3:

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )


    orb = cv2.ORB_create(
        nfeatures=ORB_FEATURE_COUNT
    )


    keypoints, descriptors = (
        orb.detectAndCompute(
            image,
            None
        )
    )


    return (
        keypoints,
        descriptors
    )


def match_features(
    descriptors1,
    descriptors2
):

    if (
        descriptors1 is None
        or
        descriptors2 is None
    ):

        return (
            [],
            [],
            0.0
        )


    matcher = cv2.BFMatcher(
        cv2.NORM_HAMMING,
        crossCheck=True
    )


    matches = matcher.match(
        descriptors1,
        descriptors2
    )


    matches = sorted(
        matches,
        key=lambda match:
            match.distance
    )


    good_matches = [

        match

        for match in matches

        if (
            match.distance
            <
            ORB_GOOD_MATCH_DISTANCE
        )

    ]


    if len(matches) == 0:

        similarity = 0.0

    else:

        similarity = (
            len(good_matches)
            /
            len(matches)
        ) * 100.0


    return (
        matches,
        good_matches,
        similarity
    )


if __name__ == "__main__":

    print()

    print(
        "======================================"
    )

    print(
        "     VEINPAY FEATURE MODULE READY"
    )

    print(
        "======================================"
    )

    print()

    print(
        "ORB feature count:",
        ORB_FEATURE_COUNT
    )

    print(
        "Temporary good-match distance:",
        ORB_GOOD_MATCH_DISTANCE
    )

    print()

    print(
        "This module will be called by recognition.py."
    )