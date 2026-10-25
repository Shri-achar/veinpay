from camera.capture_palm import (
    VeinPayCamera
)


def main():

    print()
    print(
        "======================================"
    )
    print(
        "    VEINPAY CAMERA MODULE 3 NOIR"
    )
    print(
        "======================================"
    )
    print()


    camera = VeinPayCamera()


    try:

        camera.start()


        print()
        print(
            "Camera connected successfully."
        )

        print(
            "Capturing test image..."
        )


        image_path = camera.capture(
            "module3_noir_test.jpg"
        )


        print()
        print(
            "TEST SUCCESSFUL"
        )

        print(
            "Image:"
        )

        print(
            image_path
        )


    except Exception as error:

        print()
        print(
            "TEST FAILED"
        )

        print(
            error
        )


    finally:

        camera.stop()


if __name__ == "__main__":

    main()