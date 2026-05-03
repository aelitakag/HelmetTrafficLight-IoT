import os
os.environ["LIBCAMERA_LOG_LEVELS"] = "ERROR"

from picamera2 import Picamera2
from libcamera import controls
import time
from datetime import datetime
from pathlib import Path
import cv2
import subprocess
import re


def get_screen_resolution():
    """Read the current screen resolution if possible."""
    try:
        out = subprocess.check_output(
            ["bash", "-lc", "xrandr | grep '*' | head -n 1"],
            text=True
        )
        m = re.search(r"(\d+)x(\d+)", out)
        if m:
            return int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    return 1920, 1080


def capture_image(preview_duration=5.0, save_dir="photo"):
    """Open camera preview, capture one frame, save it, and return the latest image path."""
    photo_dir = Path(save_dir)
    photo_dir.mkdir(exist_ok=True)

    picam2 = None
    saved_path = None
    latest_path = photo_dir / "latest.jpg"
    win_name = "Camera Preview"

    try:
        print("[INFO] Opening camera...")

        try:
            picam2 = Picamera2()
        except Exception as e:
            print(f"[ERROR] Camera not detected or failed to initialize: {e}")
            return None

        frame_w, frame_h = 1440, 810

        # Configure camera preview resolution
        picam2.configure(
            picam2.create_preview_configuration(
                main={"size": (frame_w, frame_h)}
            )
        )

        picam2.start()

        # Allow time for exposure and white balance stabilization
        time.sleep(2.0)

        # Apply mild image improvements (without breaking color accuracy)
        try:
            picam2.set_controls({
                "AwbEnable": True,
                "AeEnable": True,
                "AwbMode": controls.AwbModeEnum.Auto,
                "AeMeteringMode": controls.AeMeteringModeEnum.CentreWeighted,
                "NoiseReductionMode": controls.draft.NoiseReductionModeEnum.HighQuality,
                "Sharpness": 1.1,
                "Contrast": 1.03,
                "Saturation": 1.0,
                "Brightness": 0.0
            })
        except Exception:
            pass

        # Drop initial frames to ensure stable image
        for _ in range(8):
            picam2.capture_array()
            time.sleep(0.03)

        # Create full-screen preview window
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        screen_w, screen_h = get_screen_resolution()

        # Capture and display first frame
        frame0 = picam2.capture_array()
        frame0_bgr = cv2.cvtColor(frame0, cv2.COLOR_RGB2BGR)
        frame0_full = cv2.resize(frame0_bgr, (screen_w, screen_h), interpolation=cv2.INTER_LINEAR)
        cv2.imshow(win_name, frame0_full)
        cv2.waitKey(1)

        capture_time = preview_duration / 2
        start_time = time.time()
        captured = False

        print("[INFO] Camera preview started.")

        while True:
            elapsed = time.time() - start_time
            if elapsed >= preview_duration:
                break

            frame = picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Resize frame for full-screen display
            frame_full = cv2.resize(frame_bgr, (screen_w, screen_h), interpolation=cv2.INTER_LINEAR)

            cv2.imshow(win_name, frame_full)
            cv2.waitKey(1)

            # Capture image once in the middle of preview
            if (not captured) and (elapsed >= capture_time):
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

                saved_path = photo_dir / f"image_{timestamp}.jpg"

                # Save original frame (not the resized display)
                cv2.imwrite(str(saved_path), frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 98])
                cv2.imwrite(str(latest_path), frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 98])

                print(f"[INFO] Image captured successfully: {latest_path}")
                captured = True

        if not captured:
            print("[ERROR] No image was captured.")
            return None

        return str(latest_path)

    finally:
        # Close preview window
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

        # Stop camera safely
        if picam2 is not None:
            try:
                picam2.stop()
                print("[INFO] Camera closed.")
            except Exception:
                pass


if __name__ == "__main__":
    saved = capture_image()

    if saved:
        print(f"[INFO] Latest image saved to: {saved}")
    else:
        print("[ERROR] Failed to capture photo.")