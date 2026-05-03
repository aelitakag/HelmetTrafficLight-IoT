import signal
import sys

import time

from camera import capture_image
from server_connection import send_image
from traffic_light import setup_gpio, normal_cycle, set_red_mode, cleanup
from OLED import show_warning, clear_display


def cleanup_all(signum=None, frame=None):
    """Clean system state before exit."""
    try:
        clear_display()
    except Exception:
        pass

    cleanup()
    print("[INFO] System stopped cleanly.")
    sys.exit(0)


def print_result(response_data):
    """Print the server response in a readable format."""
    result = response_data.get("result", {})

    print("[INFO] JSON response received:")
    print(f"message: {response_data.get('message', 'N/A')}")
    print(f"pretty_text: {response_data.get('pretty_text', 'N/A')}")
    print("result:")
    print(f"  has_motorcycle: {result.get('has_motorcycle', 'N/A')}")
    print(f"  persons_total: {result.get('persons_total', 'N/A')}")
    print(f"  riders_total: {result.get('riders_total', 'N/A')}")
    print(f"  riders_with_helmet: {result.get('riders_with_helmet', 'N/A')}")
    print(f"  riders_without_helmet: {result.get('riders_without_helmet', 'N/A')}")
    print(f"  riders_ambiguous: {result.get('riders_ambiguous', 'N/A')}")
    print(f"  required_ratio: {result.get('required_ratio', 'N/A')}")
    print(f"  allow_green: {result.get('allow_green', 'N/A')}")
    print(f"  image_path: {result.get('image_path', 'N/A')}")


def main():
    signal.signal(signal.SIGINT, cleanup_all)
    signal.signal(signal.SIGTERM, cleanup_all)

    setup_gpio()
    clear_display()

    print("[INFO] Starting single capture and decision...")

    # capture image once
    image_path = capture_image()

    if not image_path:
        print("[ERROR] Failed to capture image.")
        print("[INFO] Fallback: running normal traffic light cycle until stopped.")
        clear_display()
        while True:
            normal_cycle()

    print(f"[INFO] Image captured: {image_path}")

    # send image to server
    response_data = send_image(image_path)

    if not response_data:
        print("[WARNING] No response from server.")
        print("[INFO] Fallback: running normal traffic light cycle until stopped.")
        clear_display()
        while True:
            normal_cycle()

    # print response
    print_result(response_data)

    # extract decision
    result = response_data.get("result", {})
    has_motorcycle = result.get("has_motorcycle", 0)
    allow_green = result.get("allow_green", True)

    # keep final state until manual stop
    if has_motorcycle == 1 and not allow_green:
        print("[INFO] Motorcycle without helmet detected -> red + blinking OLED until stopped.")
        set_red_mode()

        while True:
            show_warning(show_icon=True)
            time.sleep(0.5)
            show_warning(show_icon=False)
            time.sleep(0.5)

    else:
        print("[INFO] Normal condition -> normal traffic light cycle until stopped.")
        clear_display()

        while True:
            normal_cycle()
            clear_display()


if __name__ == "__main__":
    main()