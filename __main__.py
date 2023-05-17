'''
Displays realtime train departures for nearby stations, and upcoming events from the HU calendar.

Authored-By: Maris Baier
Co-Authored-By: Hazel Reimer
'''

import os
import re
import pathlib
import tkinter as tk
from functools import reduce
from datetime import datetime
from dateutil import parser as dateparser
import requests


from PIL import ImageTk, Image

FONT_DEFAULT = ('Helvetica', 20, 'bold')
FONT_TITLE_2 = ('Helvetica', 28, 'bold')

class OutgoingConnection:
    def __init__(self, requestjson, ypos):
        '''
        Displays departure information for a single mode of transport.

        Upon creation, checks for a correspanding lineimage stored.
        If there's none, loads an empty image.

        Then creates text objects for departure information (destination and remaining time).
        '''
        try:
            lineimage = images[requestjson['line']['name']]
        except KeyError:
            lineimage = empty
        self.image = canvas.create_image(75, ypos, image = lineimage)

        direct = requestjson['direction']
        if len(direct) > 35:
            direct = direct[0:35] + "..."
            print(direct)

        self.when_int = when_in_minutes(requestjson)

        self.direction = canvas.create_text(75+40, ypos, text=direct, font=FONT_DEFAULT, anchor='w')
        self.when = canvas.create_text(540, ypos, text=self.when_int, font=FONT_DEFAULT, anchor='e')

    def change(self, image, direction, when):
        canvas.itemconfig(self.image, image = image)
        canvas.itemconfig(self.direction, text=direction)
        canvas.itemconfig(self.when, text=when)

class Station:
    def __init__(self, config, display_offset):
        self.name = config["name"]
        self.station_id = config["station_id"]
        self.s_bahn = config["s_bahn"]
        self.tram = config["tram"]
        self.bus = config["bus"]
        self.min_time = config["min_time"]
        self.max_time = config["max_time"]
        self.min_time_needed = config["min_time_needed"]
        self.max_departures = config["max_departures"]
        self.display_offset = display_offset

        self.departures = []

        self.departures.append(canvas.create_text(50, 100+self.display_offset*40, text=self.name,font=FONT_TITLE_2, anchor='w'))
        self.departure_list()


    def departure_list(self):
        departures = get_departures(self.get_url(), self.max_departures)
        if len(departures)>len(self.departures):
            add = len(self.departures)
            for i,departure in enumerate(departures[len(self.departures):-1]):
                i += add
                self.departures.append(OutgoingConnection(departure, ypos=100+(i+self.display_offset)*40))

        for i,displayedobject in enumerate(self.departures[1:]):
            if i<len(departures):
                departure = departures[i]
                linename = departure['line']['name']
                inminutes = when_in_minutes(departure)
                
                direct = departure['direction']
                
                if len(direct) > 35:
                    direct = direct[:35] + "..."


                try:
                    displayedobject.change(images[linename],direct,inminutes)
                except KeyError:
                    if re.match("[0-9]{3}", linename) or departure['line']['adminCode'] == "SEV":
                        displayedobject.change(images['164'],direct,inminutes)
                    else:
                        displayedobject.change(empty,direct,inminutes)
                if inminutes<self.min_time_needed:
                    canvas.itemconfig(displayedobject.when, fill='red')
                else:
                    canvas.itemconfig(displayedobject.when, fill='white')
            else:
                displayedobject.change(empty,'','')
    
    def get_dep_list_length(self):
        return len(self.departures)

    def get_url(self):
        return f"https://v5.bvg.transport.rest/stops/{self.station_id}/departures?results=20&suburban={self.s_bahn}&tram={self.tram}&bus={self.bus}&when=in+{self.min_time}+minutes&duration={self.max_time-self.min_time}"

def get_departures(url, max_departures):
    while True:
        try:
            response = requests.get(url, timeout=30000).json()
        except requests.exceptions.Timeout:
            continue
        else:
            departures = []
            trip_ids = []
            for i in response:
                if i['when'] is not None and i['tripId'] not in trip_ids and len(departures) <= max_departures:
                    departures.append(i)
                    trip_ids.append(i['tripId'])
            break
    return departures

def when_in_minutes(json):
    departure = dateparser.parse(json['when'])

    difference = departure - datetime.now(departure.tzinfo)
    difference = difference.total_seconds() / 60

    return int(difference)

def get_images():
    out = []

    # https://stackoverflow.com/a/3430395
    root_path = pathlib.Path(__file__).parent.resolve()

    for f in os.scandir(root_path.joinpath("src/images/")):
        if re.match(r"S?[0-9]+\.png", f.name):
            out.append(f.name.split(".")[0])

    return out

def setup(ctx):
    ctx.create_rectangle(580, 0, 1200, 800, fill='#165096', outline='#165096')
    ctx.create_image(700, 100, image=hu_logo_image)
    ctx.pack(fill=tk.BOTH, expand=True)

    event_display_offset = 300
    for event_config in event_configs:
        ctx.create_text(650, event_display_offset, text=event_config["date"], font=FONT_DEFAULT, anchor='nw')

        for line in event_config["description"]:
            ctx.create_text(750, event_display_offset, text=line, font=FONT_DEFAULT, anchor='nw')
            event_display_offset += 25
        
        event_display_offset += 5

def load_image(acc, name):
    image = Image.open(image_path.joinpath(f"{name}.png"))
    if name.startswith("S"):
        image.thumbnail((40,40), Image.LANCZOS)
    else:
        image.thumbnail((30,30), Image.LANCZOS)
    image = ImageTk.PhotoImage(image)
    
    return {**acc, **{name: image}}


### Setup

root = tk.Tk()
root.attributes("-fullscreen", True)
canvas = tk.Canvas()

# https://stackoverflow.com/a/3430395
image_path = pathlib.Path(__file__).parent.resolve().joinpath("src/images/")

empty = Image.open(image_path.joinpath("Empty.png")).resize((1,1))
empty = ImageTk.PhotoImage(empty)

hu_logo_image = Image.open(image_path.joinpath("Huberlin-logo.png")).resize((100,100))
hu_logo_image = ImageTk.PhotoImage(hu_logo_image)

imagenames = get_images()
images = reduce(load_image, imagenames, {})


station_configs = [
    {
        "name": "S Adlershof",
        "station_id": 900193002,
        "s_bahn": True,
        "tram": False,
        "bus": True,
        "min_time": 9,
        "max_time": 42,
        "min_time_needed": 11,
        "max_departures": 6
    },
    {
        "name": "Karl-Ziegler-Str",
        "station_id": 900000194016,
        "s_bahn": False,
        "tram": True,
        "bus": False,
        "min_time": 3,
        "max_time": 28,
        "min_time_needed": 5,
        "max_departures": 5
    },
    {
        "name": "Magnusstr.",
        "station_id": 900000194501,
        "s_bahn": False,
        "tram": False,
        "bus": True,
        "min_time": 3,
        "max_time": 24,
        "min_time_needed": 5,
        "max_departures": 5
    }
]

event_configs = [
    {
        "date": "Morgen",
        "description": [
            "Auftaktsparty ab 17 Uhr!",
        ],
    },
    {
        "date": "22. Mai",
        "description": [
            "Schachturnier",
        ],
    },
    {
        "date": "30. Mai",
        "description": [
            "Mops Geburtstag",
        ],
    },
    {
        "date": "14. Juni",
        "description": [
            "Hörsaalkino Special:",
            "  \"Jim Knopf und Lukas",
            "   der Lokomotivführer\"",
            "mit Vortrag von Dr. Lohse",
        ],
    },
]

setup(canvas)

stations = []
station_display_offset = 0 # pylint: disable=invalid-name

for idx, station_config in enumerate(station_configs):
    if idx > 0:
        station_display_offset += stations[idx-1].get_dep_list_length() + 1

    stations.append(Station(station_config, station_display_offset))

def mainloop(): # pylint: disable=missing-function-docstring
    for station in stations[:1]:
        station.departure_list()

    # Refresh every minute
    root.after(60 * 1000, mainloop)

# First refresh after 1 second
root.after(1000, mainloop)
root.mainloop()
