"""Project globals
Define display properties (sizes, fonts, colors), update times and paths
"""

from pathlib import Path
from tkinter.font import Font
from typing import List, Tuple
from PIL.Image import open as open_image
from PIL.ImageTk import PhotoImage


# used fonts
# ----------
FONT_TITLE = Font(font=("Helvetica", 24, "bold"))
FONT_DEPARTURE = Font(font=("Helvetica", 17, "bold"))
FONT_EVENT = Font(font=("Helvetica", 17, "bold"))
FONT_CLOCK = Font(font=("Helvetica", 17, "bold"))

# canvas sizes
# ----------------
WIDTH_ROOT = 1280
HEIGHT_ROOT = 1024

WIDTH_STATION_CANVAS = 800
HEIGHT_STATION_CANVAS = HEIGHT_ROOT

WIDTH_EVENT_CANVAS = WIDTH_ROOT - WIDTH_STATION_CANVAS
HEIGHT_EVENT_CANVAS = HEIGHT_ROOT

# station departure sizes
# -----------------------
HEIGHT_ICON = FONT_DEPARTURE.metrics("linespace")
WIDTH_ICON = 40
WIDTH_DIRECTION = 250
WIDTH_TIME = FONT_DEPARTURE.measure("00")  # space for MM time format

# information sizes
# -----------------
WIDTH_DATE = FONT_EVENT.measure("00.00.")  # space for DD.MM. date format
HEIGHT_POSTER = 350
WIDTH_POSTER = 450
HEIGHT_LOGO = 150
WIDTH_LOGO = 450

# colors
# ------
COLOR_TXT = "#ffffff"  # for any basic text
COLOR_NOTIME = "#d22222"  # for time remaining if departure is not reachable
COLOR_ERROR = "#808080"  # to display errors on canvas
COLOR_BG_STATION = "#28282d"  # station departure background
COLOR_BG_INFO = "#4070c5"  # information background

# update times
# ------------
STATION_UPDATE_TIME = 10_000
EVENT_UPDATE_TIME = 60_000
POSTER_UPDATE_TIME = 60_000
CLOCK_UPDATE_TIME = 10_000

# resource paths
# --------------
PATH = Path(__file__).parents[1].resolve() / "data"

POSTER_PATH = PATH / "posters"
CONFIG_PATH = PATH / "config.kdl"
LOGO_PATH = PATH / "logo.png"
ICON_PATH = PATH / "lines"


def load_image(path: Path, width: int, height: int) -> PhotoImage:
    """Load a tkinter image with pillow"""
    image = open_image(path)
    image.thumbnail((width, height))
    return PhotoImage(image)


ICONS = {file.stem: load_image(file, WIDTH_ICON, HEIGHT_ICON)
         for file in ICON_PATH.glob("*.png")}
LOGO = load_image(LOGO_PATH, WIDTH_LOGO, HEIGHT_LOGO)

# direction name replacement filter
# ---------------------------------
DIRECTION_FILTER: List[Tuple[str, str]] = [
    ("Schienenersatzverkehr", "SEV"),
    ("Ersatzverkehr", "EV"),
    ("(Berlin)", ""),
    ("Bhf", ""),
    ("Flughafen BER", "BER"),
]
