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
import json

from dateutil import parser as dateparser
from PIL import ImageTk, Image
import requests

from config import events as event_configs, stations as station_configs, Station as StationConfig


FONT_DEFAULT = ("Helvetica", 17, "bold")
FONT_TITLE_2 = ("Helvetica", 28, "bold")
gui_middle = 1280*0.618

class OutgoingConnection:
    """
    Displays departure information for a single mode of transport at a single station.
    """
    def __init__(self, requestjson, xpos, ypos):
        """
        Upon creation, checks for a correspanding lineimage stored.
        If there"s none, loads an empty image.

        Then creates text objects for departure information (destination and remaining time).
        """
        lineimage = resolve_image(requestjson)

        self.image = canvas.create_image(xpos-40, ypos, image = lineimage)

        direct = requestjson["direction"]
        if len(direct) > 35:
            direct = direct[0:35] + "..."
            print(direct)

        self.when_int = calculate_remaining_time(requestjson)

        self.direction = canvas.create_text(xpos, ypos, text=direct, font=FONT_DEFAULT, anchor="w", fill="#fff")
        self.when = canvas.create_text(xpos+250, ypos, text=self.when_int, font=FONT_DEFAULT, anchor="e", fill="#fff")

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
        self.departures = [[],[]]

        self.departures[0].append(canvas.create_text(40, 60+self.display_offset*30, text=self.name,font=FONT_TITLE_2, anchor="w", fill="#fff"))  # pylint: disable=line-too-long
        self.departures[1].append(canvas.create_text(400, 60+self.display_offset*30, text='',font=FONT_TITLE_2, anchor="w", fill="#fff"))  # pylint: disable=line-too-long
        self.departure_list()


    def departure_list(self):
        """
        Diffs the displayed departure information on the canvas
        with the information provided by the API.

        If there are more departures than displayed, adds new ones.
        If there are less departures than displayed, removes the excess.

        This is done regularly to keep the displayed information up to date.
        """
        departures_direction1 = fetch_departures(self.get_url(self.direction1), self.max_departures)
        departures_direction2 = fetch_departures(self.get_url(self.direction2), self.max_departures)

        if len(departures_direction1)>len(self.departures[0]):
            add = len(self.departures[0])
            for i,departure in enumerate(departures_direction1[len(self.departures[0]):-1]):
                i += add
                connection = OutgoingConnection(departure, 100, ypos=75+(i+self.display_offset)*30)
                self.departures[0].append(connection)

        for i,displayedobject in enumerate(self.departures[0][1:]):
            if i<len(departures_direction1):
                departure = departures_direction1[i]
                time_remaining = calculate_remaining_time(departure)

                try:
                    direct = line_names[departure['direction']]
                except KeyError:
                    direct = departure['direction']
                    print(direct)

                if direct is None:
                    direct = '???'
                elif len(direct) > 35:
                    direct = direct[:35] + "..."

                lineimage = resolve_image(departure)
                displayedobject.change(lineimage, direct, time_remaining)

                if time_remaining < self.min_time_needed:
                    canvas.itemconfig(displayedobject.when, fill="red")
                else:
                    canvas.itemconfig(displayedobject.when, fill="white")
            else:
                displayedobject.change(empty,"","")

        if len(departures_direction2)>len(self.departures[1]):
            add = len(self.departures[1])
            for i,departure in enumerate(departures_direction2[len(self.departures[1]):-1]):
                i += add
                connection = OutgoingConnection(departure, 470, ypos=70+(i+self.display_offset)*30)
                self.departures[1].append(connection)

        for i,displayedobject in enumerate(self.departures[1][1:]):
            if i<len(departures_direction2):
                departure = departures_direction2[i]
                time_remaining = calculate_remaining_time(departure)

                try:
                    direct = line_names[departure['direction']]
                except KeyError:
                    direct = departure['direction']
                    print(direct)

                if direct is None:
                    direct = '???'
                elif len(direct) > 35:
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
        return max(len(self.departures[0]), len(self.departures[1]))

    def get_url(self, direction):
        """
        Constructs the URL for the API request.
        """
        return f"https://v6.bvg.transport.rest/stops/{self.station_id}/departures?direction={direction}&results=20&suburban={self.s_bahn}&tram={self.tram}&bus={self.bus}&express={self.express}&when=in+{self.min_time}+minutes&duration={self.max_time-self.min_time}"  # pylint: disable=line-too-long
    
    def disable(self):
        '''
        Hints that departures couldn't be fetched
        '''
        for outgoingconnection in self.departures[0][1:]:
            outgoingconnection.change(empty, '''couldn't fetch''', '', fill='grey')
        for outgoingconnection in self.departures[1][1:]:
            outgoingconnection.change(empty, '''couldn't fetch''', '', fill='grey')

def fetch_departures(url, max_departures):
    """
    Requests the API for departure information.
    """
    response = session.get(url, timeout=30_000).json()
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
    if departure["line"]["name"] is None:
        name = '???'
    else:
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
    Sets up the initial canvas state. Display resolution at Mops is 1280x1024.
    This includes the background, the logo and the event information.
    """
    global clock
    ctx.config(bg='#141416')
    ctx.create_rectangle(gui_middle, 0, 1280, 1024, fill="#165096", outline="#165096")
    ctx.create_image(gui_middle+100, 100, image=hu_logo_image)
    clock = ctx.create_text(gui_middle+270, 70, font=FONT_TITLE_2, fill='#fff', text=datetime.now().strftime('%H:%M'), )
    #ctx.create_image(gui_middle+175, 475, image=Ringbahn_Image)
    ctx.create_image(gui_middle+50, 350, image=Doko_Image, anchor="nw")
    #ctx.create_text(gui_middle+250, 500, text="RINGBAHNTOUR\nSAUFEN\nLETSGOOOOO", fil='#fff')
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

# https://www.codeproject.com/Questions/1008506/python-requests-package-very-slow-retrieving-html
session = requests.Session()
session.trust_env = False

# https://stackoverflow.com/a/3430395
path = pathlib.Path(__file__).parent.resolve()
image_path = path / "src/images/"

empty = Image.open(image_path.joinpath("Empty.png")).resize(size=(1,1))
empty = ImageTk.PhotoImage(empty)

Ringbahn_Image = Image.open(image_path.joinpath('1.jpg')).resize(size=(240,240))
Ringbahn_Image = ImageTk.PhotoImage(Ringbahn_Image)

Doko_Image = Image.open(image_path.joinpath('doko_plakat.png')).resize(size=(320,445))
Doko_Image = ImageTk.PhotoImage(Doko_Image)

hu_logo_image = Image.open(image_path.joinpath("Huberlin-logo.png")).resize(size=(100,100))
hu_logo_image = ImageTk.PhotoImage(hu_logo_image)

images = {
    file.stem: load_image(file)
    for file in (image_path).glob("*.png")
}

line_names = json.load(open(path / "line_names.json", encoding='utf-8'))

setup(canvas)

stations = []
station_display_offset = 0

for idx, station_config in enumerate(station_configs):
    if idx > 0:
        station_display_offset += stations[idx-1].get_departure_count() + 1.5

    stations.append(Station(**asdict(station_config), display_offset=station_display_offset))

def mainloop():  # pylint: disable=missing-function-docstring
    for station in stations:
        try:
            station.departure_list()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError, TypeError):
            station.disable()
    canvas.itemconfig(clock, text=datetime.now().strftime('%H:%M'))

    # Refresh every five seconds
    root.after(5_000, mainloop)

# First refresh after five seconds
root.after(5_000, mainloop)

root.mainloop()
