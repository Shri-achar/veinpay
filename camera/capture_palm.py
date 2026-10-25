from datetime import datetime
from pathlib import Path
import time

from picamera2 import Picamera2
from libcamera import controls

from config import (
    CAPTURED_IMAGES_DIR,
    CAMERA_WIDTH,
    CAMERA_HEIGHT
)


# ============================================================
# CAMERA CLASS
# ============================================================

class VeinPayCamera:

    def __init__(self):

        self.camera = None
        self.started = False


    # ========================================================
    # START CAMERA
    # ========================================================

    def start(self):

        if self.started:
            return

        print("Starting VeinPay Camera Module 3 NoIR...")


        self.camera = Picamera2()


        config = self.camera.create_still_configuration(
            main={
                "size": (
                    CAMERA_WIDTH,
                    CAMERA_HEIGHT
                )
            }
        )


        self.camera.configure(
            config
        )


        # Camera Module 3 supports autofocus
        self.camera.set_controls(
            {
                "AfMode":
                    controls.AfModeEnum.Continuous
            }
        )


        self.camera.start()


        # Allow exposure + autofocus to settle
        time.sleep(2)


        self.started = True


        print(
            "Camera ready."
        )


    # ========================================================
    # CAPTURE IMAGE
    # ========================================================

    def capture(
        self,
        filename=None
    ):

        if not self.started:

            self.start()


        capture_folder = Path(
            CAPTURED_IMAGES_DIR
        )


        capture_folder.mkdir(
            parents=True,
            exist_ok=True
        )


        if filename is None:

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            filename = (
                f"palm_{timestamp}.jpg"
            )


        output_path = (
            capture_folder
            /
            filename
        )


        print(
            "Capturing palm image..."
        )


        self.camera.capture_file(
            str(output_path)
        )


        print(
            f"Image saved: {output_path}"
        )


        return str(
            output_path
        )


    # ========================================================
    # STOP CAMERA
    # ========================================================

    def stop(self):

        if (
            self.camera is not None
            and
            self.started
        ):

            self.camera.stop()

            self.camera.close()


        self.camera = None
        self.started = False


        print(
            "Camera stopped."
        )


# ============================================================
# SIMPLE FUNCTION FOR MAIN PROJECT
# ============================================================

def capture_palm_image(
    filename=None
):

    camera = VeinPayCamera()


    try:

        camera.start()

        image_path = camera.capture(
            filename
        )

        return image_path


    finally:

        camera.stop()


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "======================================"
    )
    print(
        "      VEINPAY CAMERA CAPTURE TEST"
    )
    print(
        "======================================"
    )
    print()


    try:

        path = capture_palm_image(
            "camera_test.jpg"
        )


        print()
        print(
            "SUCCESS"
        )

        print(
            "Captured:"
        )

        print(
            path
        )


    except Exception as error:

        print()
        print(
            "CAMERA TEST FAILED"
        )

        print(
            error
        )