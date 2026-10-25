from picamera2 import Picamera2
import cv2


picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={
        "size": (640, 480),
        "format": "RGB888"
    }
)

picam2.configure(config)
picam2.start()


print("VeinPay live camera started")
print("Press Q to close")


while True:

    frame = picam2.capture_array()

    cv2.imshow(
        "VeinPay Live Camera",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cv2.destroyAllWindows()
picam2.stop()
