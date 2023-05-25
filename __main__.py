"""
Displays realtime train departures for nearby stations, and upcoming events from the HU calendar.

Authored-By: Maris Baier
Co-Authored-By: Hazel Reimer
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
import pathlib
import re
import tkinter as tk

from dateutil import parser as dateparser
from PIL import ImageTk, Image
import requests

from config import events as event_configs, stations as station_configs, Station as StationConfig


FONT_DEFAULT = ("Helvetica", 14, "bold")
FONT_TITLE_2 = ("Helvetica", 24, "bold")
gui_middle = 768/1.17

class OutgoingConnection:
    """
    Displays departure information for a single mode of transport at a single station.
    """
    def __init__(self, requestjson, ypos):
        """
        Upon creation, checks for a correspanding lineimage stored.
        If there"s none, loads an empty image.

        Then creates text objects for departure information (destination and remaining time).
        """
        lineimage = resolve_image(requestjson)

        self.image = canvas.create_image(75, ypos, image = lineimage)

        direct = requestjson["direction"]
        if len(direct) > 35:
            direct = direct[0:35] + "..."
            print(direct)

        self.when_int = calculate_remaining_time(requestjson)

        self.direction = canvas.create_text(75+40, ypos, text=direct, font=FONT_DEFAULT, anchor="w", fill="#fff")
        self.when = canvas.create_text(540, ypos, text=self.when_int, font=FONT_DEFAULT, anchor="e", fill="#fff")

    def change(self, image, direction, when, fill='white'):
        """
        Updates the displayed information on the canvas with the provided parameters.
        """
        canvas.itemconfig(self.image, image = image)
        canvas.itemconfig(self.direction, text=direction, fill=fill)
        canvas.itemconfig(self.when, text=when, fill=fill)

@dataclass
class Station(StationConfig):
    """
    Displays realtime departure information for a single station.
    """
    display_offset: int
    departures: list = field(init=False)

    def __post_init__(self):
        self.departures = []

        self.departures.append(canvas.create_text(50, 60+self.display_offset*30, text=self.name,font=FONT_TITLE_2, anchor="w", fill="#fff"))  # pylint: disable=line-too-long
        self.departure_list()


    def departure_list(self):
        """
        Diffs the displayed departure information on the canvas
        with the information provided by the API.

        If there are more departures than displayed, adds new ones.
        If there are less departures than displayed, removes the excess.

        This is done regularly to keep the displayed information up to date.
        """
        try:
            departures = fetch_departures(self.get_url(), self.max_departures)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
            self.disable()
        else:
            if len(departures)>len(self.departures):
                add = len(self.departures)
                for i,departure in enumerate(departures[len(self.departures):-1]):
                    i += add
                    connection = OutgoingConnection(departure, ypos=70+(i+self.display_offset)*30)
                    self.departures.append(connection)

            for i,displayedobject in enumerate(self.departures[1:]):
                if i<len(departures):
                    departure = departures[i]
                    time_remaining = calculate_remaining_time(departure)

                    direct = departure["direction"]

                    if len(direct) > 35:
                        direct = direct[:35] + "..."


                    lineimage = resolve_image(departure)
                    displayedobject.change(lineimage, direct, time_remaining)

                    if time_remaining < self.min_time_needed:
                        canvas.itemconfig(displayedobject.when, fill="red")
                    else:
                        canvas.itemconfig(displayedobject.when, fill="white")
                else:
                    displayedobject.change(empty,"","")

    def get_departure_count(self):
        """
        Returns the number of departures currently displayed.
        """
        return len(self.departures)

    def get_url(self):
        """
        Constructs the URL for the API request.
        """
        return f"https://v6.bvg.transport.rest/stops/{self.station_id}/departures?results=20&suburban={self.s_bahn}&tram={self.tram}&bus={self.bus}&express={self.express}&when=in+{self.min_time}+minutes&duration={self.max_time-self.min_time}"  # pylint: disable=line-too-long
    
    def disable(self):
        '''
        Hints that departures couldn't be fetched
        '''
        for outgoingconnection in self.departures[1:]:
            outgoingconnection.change(empty, '''couldn't fetch''', '', fill='grey')

def fetch_departures(url, max_departures):
    """
    Requests the API for departure information.
    """
    response = requests.get(url, timeout=30000).json()
    departures = []
    trip_ids = []
    for departure in response['departures']:
        trip_id = departure["tripId"]

        is_in_trip_ids = trip_id in trip_ids
        is_scheduled = departure["when"] is not None
        if is_scheduled and not is_in_trip_ids and len(departures) <= max_departures:
            departures.append(departure)
            trip_ids.append(trip_id)
    return departures

def calculate_remaining_time(json):
    """
    Calculates the remaining time until departure.
    Returns the time in minutes.
    """
    departure = dateparser.parse(json["when"])

    difference = departure - datetime.now(departure.tzinfo)
    difference = difference.total_seconds() / 60

    return int(difference)

def resolve_image(departure):
    """
    Returns the line image for the given line name.
    """

    name = departure["line"]["name"]
    admin_code = departure["line"]["adminCode"]

    if name in images:
        return images[name]
    else:
        if re.match(r"(\d{3}|N\d{2,3})", name) or admin_code == "SEV":
            print(f"Using fallback image for bus '{name}'.")
            return images["bus"]
        elif re.match(r"(M?\d{2})", name):
            print(f"Using fallback image for tram '{name}'.")
            return images["tram"]
        else:
            print(f"Image not found for '{name}'.")
            return empty

def setup(ctx):
    """
    Sets up the initial canvas state. Display resolution at Mops is 1280x1024
    This includes the background, the logo and the event information.
    """
    global clock
    ctx.config(bg='#141416')
    ctx.create_rectangle(gui_middle, 0, 1280, 1024, fill="#165096", outline="#165096")
    ctx.create_image(gui_middle+100, 100, image=hu_logo_image)
    clock = ctx.create_text(gui_middle+270, 70, text=datetime.now().strftime('%H:%M'), font=FONT_TITLE_2, fill='#fff')
    ctx.create_image(gui_middle+150, 500, image=RingbahnImage)
    ctx.create_text(gui_middle+250, 500, text="RINGBAHNTOUR\nSAUFEN\nLETSGOOOOO", fil='#fff')
    #ctx.create_image(1000, 680, image=bike_route_image)
    ctx.pack(fill=tk.BOTH, expand=True)

    event_display_offset = 250
    ctx.create_text(gui_middle+50, event_display_offset-35, text='Nächste Veranstaltungen:', font=FONT_DEFAULT, anchor="nw", fill='#fff')
    for event_config in event_configs:
        ctx.create_text(gui_middle+50, event_display_offset, text=event_config.date, font=FONT_DEFAULT, anchor="nw", fill="#fff")  # pylint: disable=line-too-long

        for line in event_config.text.split("\n"):
            ctx.create_text(gui_middle+130, event_display_offset, text=line, font=FONT_DEFAULT, anchor="nw", fill="#fff")
            event_display_offset += 25

        event_display_offset += 5

def load_image(file: pathlib.Path):
    """
    Loads an image for one of the connections from the src/images folder.
    """
    image = Image.open(file)
    if file.name.startswith("S"):
        image.thumbnail((40,40), Image.LANCZOS)
    else:
        image.thumbnail((30,30), Image.LANCZOS)
    image = ImageTk.PhotoImage(image)

    return image


### Setup

root = tk.Tk()
root.attributes("-fullscreen", True)
#root.geometry("1024x768")
canvas = tk.Canvas()

# https://stackoverflow.com/a/3430395
image_path = pathlib.Path(__file__).parent.resolve() / "src/images/"

empty = Image.open(image_path.joinpath("Empty.png")).resize(size=(1,1))
empty = ImageTk.PhotoImage(empty)

RingbahnImage = ImageTk.PhotoImage(Image.open(image_path.joinpath('Ringbahntour.png')).resize(size=(200, 350)))

hu_logo_image = Image.open(image_path.joinpath("Huberlin-logo.png")).resize(size=(100,100))
hu_logo_image = ImageTk.PhotoImage(hu_logo_image)

bike_route_image = Image.open(image_path.joinpath("bike_route.png")).resize(size=(400,415))
bike_route_image = ImageTk.PhotoImage(bike_route_image)

images = {
    file.stem: load_image(file)
    for file in (image_path).glob("*.png")
}

setup(canvas)

stations = []
station_display_offset = 0

for idx, station_config in enumerate(station_configs):
    if idx > 0:
        station_display_offset += stations[idx-1].get_departure_count() + 1

    stations.append(Station(**asdict(station_config), display_offset=station_display_offset))

def mainloop():  # pylint: disable=missing-function-docstring
    for station in stations:
        station.departure_list()
    canvas.itemconfig(clock, text=datetime.now().strftime('%H:%M'))

    # Refresh every minute
    root.after(5_000, mainloop)

# First refresh after 1 second
root.after(5_000, mainloop)
root.mainloop()
