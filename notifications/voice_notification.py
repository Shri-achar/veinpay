
from pathlib import Path
from decimal import Decimal
import subprocess
import threading
import logging

AUDIO_DIR = Path(__file__).resolve().parent / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def format_amount(amount):
    """Convert payment amount into spoken rupees and paise."""
    value = Decimal(str(amount)).quantize(Decimal("0.01"))
    rupees = int(value)
    paise = int((value - rupees) * 100)

    if paise:
        return f"{rupees} rupees and {paise} paise"

    return f"{rupees} rupees"


def generate_voice(message, filename):
    """Generate WAV without requiring an audio device."""
    output = AUDIO_DIR / filename

    subprocess.run(
        [
            "espeak-ng",
            "-v", "en-in",
            "-s", "145",
            "-w", str(output),
            message
        ],
        check=True,
        timeout=15
    )

    return output


def announce(event, amount):
    """
    Queue voice generation in a background thread.
    No physical speaker required yet.
    """
    messages = {
        "initiated": f"{format_amount(amount)} payment initiated.",
        "success": f"{format_amount(amount)} paid successfully.",
        "failed": f"{format_amount(amount)} payment unsuccessful."
    }

    if event not in messages:
        return

    def worker():
        try:
            filename = f"payment_{event}.wav"
            generate_voice(messages[event], filename)
            print(f"VeinPay voice: {messages[event]}")
        except Exception:
            logging.exception("VeinPay voice generation failed")

    threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    import time

    announce("initiated", 50)
    announce("success", 50)
    announce("failed", 50)

    time.sleep(2)
