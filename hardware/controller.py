import time

import board
import busio
import adafruit_ssd1306
import adafruit_vl53l0x

from PIL import (
    Image,
    ImageDraw,
    ImageFont
)


# ============================================================
# VEINPAY HARDWARE CONTROLLER
# ============================================================

class VeinGateHardwareController:

    def __init__(self):

        # ----------------------------------------------------
        # HARDWARE STATUS
        # ----------------------------------------------------

        self.distance_sensor_available = False
        self.temperature_sensor_available = False
        self.oled_available = False
        self.ir_led_available = False
        self.buzzer_available = False


        # ----------------------------------------------------
        # SENSOR VALUES
        # ----------------------------------------------------

        self.distance_cm = None
        self.temperature_c = None


        # ----------------------------------------------------
        # SHARED I2C BUS
        # ----------------------------------------------------

        self.i2c = None


        # ----------------------------------------------------
        # OLED
        # ----------------------------------------------------

        self.display = None


        # ----------------------------------------------------
        # TOF
        # ----------------------------------------------------

        self.tof_sensor = None


        # ----------------------------------------------------
        # OLED FONTS
        # ----------------------------------------------------

        try:

            self.font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                20
            )

            self.font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                16
            )

        except Exception:

            print(
                "DejaVu font not found. "
                "Using default OLED font."
            )

            self.font_large = (
                ImageFont.load_default()
            )

            self.font_small = (
                ImageFont.load_default()
            )


    # ========================================================
    # INITIALIZE HARDWARE
    # ========================================================

    def initialize(self):

        print()
        print(
            "Initializing VeinPay hardware..."
        )


        # Create I2C bus once
        self.initialize_i2c()


        # Initialize devices
        self.initialize_oled()

        self.initialize_tof()


        print(
            "Hardware initialization complete."
        )

        print(
            self.get_status()
        )

        print()


        return self.get_status()


    # ========================================================
    # INITIALIZE I2C
    # ========================================================

    def initialize_i2c(self):

        try:

            if self.i2c is None:

                self.i2c = busio.I2C(
                    board.SCL,
                    board.SDA
                )


            print(
                "I2C bus initialized."
            )


        except Exception as error:

            print(
                "I2C initialization failed:",
                error
            )

            self.i2c = None


    # ========================================================
    # INITIALIZE OLED
    # ========================================================

    def initialize_oled(self):

        try:

            if self.i2c is None:

                self.initialize_i2c()


            self.display = (
                adafruit_ssd1306.SSD1306_I2C(
                    128,
                    64,
                    self.i2c
                )
            )


            self.display.fill(0)

            self.display.show()


            self.oled_available = True


            print(
                "OLED initialized successfully."
            )


            self.show_idle()


        except Exception as error:

            self.oled_available = False


            print(
                "OLED initialization failed:",
                error
            )


    # ========================================================
    # INITIALIZE TOF SENSOR
    # ========================================================

    def initialize_tof(self):

        try:

            if self.i2c is None:

                self.initialize_i2c()


            self.tof_sensor = (
                adafruit_vl53l0x.VL53L0X(
                    self.i2c
                )
            )


            # Read once to verify sensor
            distance_mm = (
                self.tof_sensor.range
            )


            self.distance_cm = (
                distance_mm
                /
                10.0
            )


            self.distance_sensor_available = True


            print(
                "VL53L0X initialized successfully."
            )

            print(
                f"Initial distance: "
                f"{self.distance_cm:.1f} cm"
            )


        except Exception as error:

            self.distance_sensor_available = False

            self.tof_sensor = None

            self.distance_cm = None


            print(
                "VL53L0X initialization failed:",
                error
            )


    # ========================================================
    # GET HARDWARE STATUS
    # ========================================================

    def get_status(self):

        return {

            "distance_sensor":
                self.distance_sensor_available,

            "temperature_sensor":
                self.temperature_sensor_available,

            "oled":
                self.oled_available,

            "ir_led":
                self.ir_led_available,

            "buzzer":
                self.buzzer_available
        }


    # ========================================================
    # READ TOF DISTANCE
    # ========================================================

    def get_distance_cm(self):

        if (
            not self.distance_sensor_available
            or
            self.tof_sensor is None
        ):

            return None


        try:

            distance_mm = (
                self.tof_sensor.range
            )


            self.distance_cm = (
                distance_mm
                /
                10.0
            )


            return self.distance_cm


        except Exception as error:

            print(
                "ToF read error:",
                error
            )


            self.distance_sensor_available = False

            self.distance_cm = None


            return None


    # ========================================================
    # CHECK PALM DISTANCE
    # ========================================================

    def palm_in_scan_zone(
        self,
        min_cm=5.0,
        max_cm=10.0
    ):

        distance = (
            self.get_distance_cm()
        )


        if distance is None:

            return False


        return (
            min_cm
            <=
            distance
            <=
            max_cm
        )


    # ========================================================
    # OLED MESSAGE
    # ========================================================

    def show_message(
        self,
        line1,
        line2=""
    ):

        if not self.oled_available:

            print(
                "[OLED]",
                line1,
                line2
            )

            return


        try:

            image = Image.new(
                "1",
                (
                    self.display.width,
                    self.display.height
                )
            )


            draw = ImageDraw.Draw(
                image
            )


            draw.text(
                (2, 2),
                str(line1),
                font=self.font_large,
                fill=255
            )


            if line2:

                draw.text(
                    (2, 36),
                    str(line2),
                    font=self.font_small,
                    fill=255
                )


            self.display.image(
                image
            )

            self.display.show()


        except Exception as error:

            print(
                "OLED display error:",
                error
            )


    # ========================================================
    # IDLE DISPLAY
    # ========================================================

    def show_idle(self):

        self.show_message(
            "VEINPAY",
            "Ready"
        )


    # ========================================================
    # PAYMENT REQUEST DISPLAY
    # ========================================================

    def show_payment_request(
        self,
        amount
    ):

        try:

            amount_text = (
                f"Rs.{float(amount):.0f}"
            )

        except Exception:

            amount_text = "PAYMENT"


        self.show_message(
            amount_text,
            "Place Palm"
        )


    # ========================================================
    # PAYMENT POSITION / TOF DISPLAY
    # ========================================================

    def show_payment_position(
        self,
        amount,
        distance_cm=None,
        min_cm=5.0,
        max_cm=10.0
    ):

        try:
            amount_text = f"Rs.{float(amount):.0f}"
        except Exception:
            amount_text = "PAYMENT"

        if distance_cm is None:

            self.show_message(
                amount_text,
                "Place Palm"
            )

            return

        try:
            distance = float(distance_cm)
        except (TypeError, ValueError):
            self.show_message(
                amount_text,
                "Place Palm"
            )
            return

        if distance > max_cm:

            self.show_message(
                amount_text,
                f"CLOSER {distance:.1f}cm"
            )

        elif distance < min_cm:

            self.show_message(
                amount_text,
                f"BACK {distance:.1f}cm"
            )

        else:

            self.show_message(
                amount_text,
                f"READY {distance:.1f}cm"
            )


    # ========================================================
    # SCANNING DISPLAY
    # ========================================================

    def show_scanning(self):

        self.show_message(
            "SCAN",
            "Hold Palm"
        )


    # ========================================================
    # RECOGNIZED DISPLAY
    # ========================================================

    def show_recognized(self):

        self.show_message(
            "FOUND",
            "Processing"
        )


    # ========================================================
    # PAYMENT SUCCESS DISPLAY
    # ========================================================

    def show_payment_success(
        self,
        amount=None
    ):

        if amount is None:

            line2 = "Complete"

        else:

            try:

                line2 = (
                    f"Rs.{float(amount):.0f} Paid"
                )

            except Exception:

                line2 = "Complete"


        self.show_message(
            "SUCCESS",
            line2
        )


    # ========================================================
    # ACCESS DENIED DISPLAY
    # ========================================================

    def show_access_denied(self):

        self.show_message(
            "DENIED",
            "Try Again"
        )


    # ========================================================
    # CALIBRATION DISPLAY
    # ========================================================

    def show_calibration_required(self):

        self.show_message(
            "NOT READY",
            "Calibrate"
        )


    # ========================================================
    # PAYMENT FAILURE DISPLAY
    # ========================================================

    def show_payment_failed(self):

        self.show_message(
            "FAILED",
            "Try Again"
        )


    # ========================================================
    # TEMPORARY MESSAGE THEN IDLE
    # ========================================================

    def show_then_idle(
        self,
        line1,
        line2="",
        seconds=2
    ):

        self.show_message(
            line1,
            line2
        )


        time.sleep(
            seconds
        )


        self.show_idle()


    # ========================================================
    # CLEAR OLED
    # ========================================================

    def clear_oled(self):

        if not self.oled_available:

            return


        try:

            self.display.fill(0)

            self.display.show()


        except Exception as error:

            print(
                "OLED clear error:",
                error
            )


    # ========================================================
    # TEMPERATURE PLACEHOLDER
    # ========================================================

    def get_temperature_c(self):

        return self.temperature_c


    # ========================================================
    # IR LED PLACEHOLDER
    # ========================================================

    def ir_on(self):

        print(
            "[IR LED] ON"
        )


    def ir_off(self):

        print(
            "[IR LED] OFF"
        )


    # ========================================================
    # BUZZER PLACEHOLDER
    # ========================================================

    def success_beep(self):

        print(
            "[BUZZER] Success"
        )


    def failure_beep(self):

        print(
            "[BUZZER] Failure"
        )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    hardware = (
        VeinGateHardwareController()
    )


    hardware.initialize()


    print(
        "Hardware status:"
    )

    print(
        hardware.get_status()
    )


    print()

    print(
        "Reading distance..."
    )


    try:

        while True:

            distance = (
                hardware.get_distance_cm()
            )


            if distance is None:

                print(
                    "ToF not available"
                )

            else:

                print(
                    f"Distance: "
                    f"{distance:.1f} cm"
                )


                if hardware.palm_in_scan_zone():

                    print(
                        "PALM IN SCAN ZONE"
                    )


            time.sleep(
                0.5
            )


    except KeyboardInterrupt:

        print()
        print(
            "Stopped"
        )

        hardware.show_idle()