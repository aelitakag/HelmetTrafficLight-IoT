import RPi.GPIO as GPIO
import time

# pins
RED_PIN = 17
YELLOW_PIN = 27
GREEN_PIN = 22

ON = True
OFF = False


def setup_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # set all traffic light pins as output
    GPIO.setup(RED_PIN, GPIO.OUT, initial=OFF)
    GPIO.setup(YELLOW_PIN, GPIO.OUT, initial=OFF)
    GPIO.setup(GREEN_PIN, GPIO.OUT, initial=OFF)


def set_lights(red=False, yellow=False, green=False):
    GPIO.output(RED_PIN, ON if red else OFF)
    GPIO.output(YELLOW_PIN, ON if yellow else OFF)
    GPIO.output(GREEN_PIN, ON if green else OFF)


def all_off():
    try:
        GPIO.output(RED_PIN, OFF)
        GPIO.output(YELLOW_PIN, OFF)
        GPIO.output(GREEN_PIN, OFF)
    except Exception:
        pass


def normal_cycle():
    # normal traffic light order
    set_lights(red=True, yellow=False, green=False)
    time.sleep(3)

    set_lights(red=True, yellow=True, green=False)
    time.sleep(1)

    set_lights(red=False, yellow=False, green=True)
    time.sleep(3)

    set_lights(red=False, yellow=True, green=False)
    time.sleep(1)


def set_red_mode():
    set_lights(red=True, yellow=False, green=False)


def cleanup():
    try:
        all_off()
        time.sleep(0.1)
    finally:
        try:
            GPIO.cleanup()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        setup_gpio()
        normal_cycle()
    finally:
        cleanup()