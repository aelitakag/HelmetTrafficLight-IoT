import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7735

spi = board.SPI()
cs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D25)
rst = digitalio.DigitalInOut(board.D24)

disp = st7735.ST7735R(
    spi,
    cs=cs,
    dc=dc,
    rst=rst,
    width=128,
    height=160,
    rotation=0,
    baudrate=24000000,
)

try:
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        14
    )
except Exception:
    font = ImageFont.load_default()


def draw_warning_screen(show_icon=True):
    w, h = 160, 128
    img = Image.new("RGB", (w, h), "black")
    draw = ImageDraw.Draw(img)

    lines = [
        "RIDER: NO HELMET",
        "TRAFFIC LIGHT",
        "DELAYED TO RED"
    ]

    line_h = font.getbbox("A")[3] + 6
    total_text_h = line_h * len(lines)
    start_y = (h - total_text_h) // 2 - 12

    for i, text in enumerate(lines):
        text_w = font.getbbox(text)[2]
        x = (w - text_w) // 2
        y = start_y + i * line_h
        draw.text((x, y), text, font=font, fill="white")

    if show_icon:
        cx = w // 2
        cy = start_y + total_text_h + 20
        r = 14
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(0, 0, 220))
        draw.rectangle((cx - 2, cy - 8, cx + 2, cy + 5), fill="white")
        draw.ellipse((cx - 2, cy + 7, cx + 2, cy + 11), fill="white")

    return img.rotate(90, expand=True)


def show_warning(show_icon=True):
    disp.image(draw_warning_screen(show_icon=show_icon))


def clear_display():
    blank = Image.new("RGB", (160, 128), "black")
    disp.image(blank.rotate(90, expand=True))