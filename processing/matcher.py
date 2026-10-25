import cv2


def compare_palms(image1_path, image2_path, label1, label2):

    img1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)

    if img1 is None:
        raise FileNotFoundError(f"Image not found: {image1_path}")

    if img2 is None:
        raise FileNotFoundError(f"Image not found: {image2_path}")

    # ORB feature detector
    orb = cv2.ORB_create(nfeatures=1000)

    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)

    if des1 is None or des2 is None:
        print(f"{label1} vs {label2}: Not enough features detected.")
        return 0

    # Brute-force matcher
    matcher = cv2.BFMatcher(
        cv2.NORM_HAMMING,
        crossCheck=True
    )

    matches = matcher.match(des1, des2)

    # Sort by best distance
    matches = sorted(
        matches,
        key=lambda x: x.distance
    )

    # Temporary good-match threshold
    good_matches = [
        match for match in matches
        if match.distance < 50
    ]

    total_matches = len(matches)
    good_count = len(good_matches)

    if total_matches > 0:
        similarity = (
            good_count / total_matches
        ) * 100
    else:
        similarity = 0

    print()
    print("========================================")
    print(f"{label1} VS {label2}")
    print("========================================")

    print(f"{label1} keypoints:", len(kp1))
    print(f"{label2} keypoints:", len(kp2))

    print("Total matches:", total_matches)
    print("Good matches:", good_count)

    print(
        f"Temporary similarity score: "
        f"{similarity:.2f}%"
    )

    # Draw top matches
    result_image = cv2.drawMatches(
        img1,
        kp1,
        img2,
        kp2,
        good_matches[:50],
        None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
    )

    # Save result
    safe_label1 = label1.replace(" ", "_")
    safe_label2 = label2.replace(" ", "_")

    output_path = (
        f"captured_images/"
        f"{safe_label1}_vs_{safe_label2}.png"
    )

    cv2.imwrite(
        output_path,
        result_image
    )

    print("Matching result saved:")
    print(output_path)

    cv2.imshow(
        f"{label1} vs {label2}",
        result_image
    )

    return similarity


if __name__ == "__main__":

    palm1 = "captured_images/processed/04_frangi.png"
    palm2 = "captured_images/processed2/04_frangi.png"
    palm3 = "captured_images/processed3/04_frangi.png"

    try:

        score_12 = compare_palms(
            palm1,
            palm2,
            "Palm 1",
            "Palm 2"
        )

        score_13 = compare_palms(
            palm1,
            palm3,
            "Palm 1",
            "Palm 3"
        )

        print()
        print("========================================")
        print("FINAL COMPARISON")
        print("========================================")

        print(
            f"Palm 1 vs Palm 2: "
            f"{score_12:.2f}%"
        )

        print(
            f"Palm 1 vs Palm 3: "
            f"{score_13:.2f}%"
        )

        print()
        print(
            "These are temporary software-test scores only."
        )

        print(
            "Do not use them yet as the final biometric threshold."
        )

        print()
        print(
            "Press any key on an image window to close."
        )

        cv2.waitKey(0)
        cv2.destroyAllWindows()

    except FileNotFoundError as error:

        print()
        print("ERROR:")
        print(error)