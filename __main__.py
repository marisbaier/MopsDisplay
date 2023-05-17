'''
This python script is used to display information on a screen:)

Author: Maris Baier
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

class SbahnObject:
    def __init__(self, requestjson, ypos):
        '''
        When an S-Bahn object is created, it checks for a correspanding lineimage stored.
        If there's none, it shows an empty image.
        It then creates text (direction and departure in min).
        '''
        try:
            lineimage = images[requestjson['line']['name']]
        except KeyError:
            lineimage = empty
        self.image = canvas.create_image(130, ypos, image = lineimage)

        direct = requestjson['direction']
        if len(direct) > 15:
            direct = direct[0:15] + "..."
            print(direct)

        self.when_int = when_in_minutes(requestjson)

        self.direction = canvas.create_text(170, ypos, text=direct,font=('Helvetica',20,'bold'), anchor='w')
        self.when = canvas.create_text(480, ypos, text=self.when_int,font=('Helvetica',20,'bold'), anchor='w')

    def change(self, image, direction, when):
        canvas.itemconfig(self.image, image = image)
        canvas.itemconfig(self.direction, text=direction)
        canvas.itemconfig(self.when, text=when)

class Station:
    def __init__(self, name, station_id, s_bahn, tram, bus, start_from=5, up_to=33, distance=11, max_departures=6, display_offset=0):
        self.name = name
        self.station_id = station_id
        self.s_bahn = s_bahn
        self.tram = tram
        self.bus = bus
        self.display_offset = display_offset
        self.start_from = start_from
        self.up_to = up_to
        self.distance = distance
        self.max_departures = max_departures

        self.dObs = []

        self.dObs.append(canvas.create_text(50, 100+self.display_offset*40, text=self.name,font=('Helvetica',28,'bold'), anchor='w'))
        self.departure_list()


    def departure_list(self):
        s_bahn_departures = get_departures(self.get_url(), self.max_departures)
        if len(s_bahn_departures)>len(self.dObs):
            add = len(self.dObs)
            for i,s_bahn in enumerate(s_bahn_departures[len(self.dObs):-1]):
                i += add
                self.dObs.append(SbahnObject(s_bahn, ypos=100+(i+self.display_offset)*40))

        for i,displayedobject in enumerate(self.dObs[1:]):
            if i<len(s_bahn_departures):
                s_bahn = s_bahn_departures[i]
                linename = s_bahn['line']['name']
                inminutes = when_in_minutes(s_bahn)
                
                direct = s_bahn['direction']
                
                if len(direct) > 15:
                    direct = direct[:15] + "..."


                try:
                    displayedobject.change(images[linename],direct,inminutes)
                except KeyError:
                    if re.match("[0-9]{3}", linename) or s_bahn['line']['adminCode'] == "SEV":
                        displayedobject.change(images['164'],direct,inminutes)
                    else:
                        displayedobject.change(empty,direct,inminutes)
                if inminutes<self.distance:
                    canvas.itemconfig(displayedobject.when, fill='red')
                else:
                    canvas.itemconfig(displayedobject.when, fill='black')
            else:
                displayedobject.change(empty,'','')
    
    def get_dep_list_length(self):
        return len(self.dObs)

    def get_url(self):
        return f"https://v5.bvg.transport.rest/stops/{self.station_id}/departures?results=20&suburban={self.s_bahn}&tram={self.tram}&bus={self.bus}&when=in+{self.start_from}+minutes&duration={self.up_to}"

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
    ctx.create_rectangle(580, 0, 1200, 800, fill='light blue', outline='light blue')
    ctx.create_image(700, 100, image=hu_logo_image)
    #ctx.create_text(480, 55, text='min', font=('Helvetica',15,'bold'))           # min sign
    ctx.pack(fill=tk.BOTH, expand=True)
    ctx.create_text(600, 300, text='Nächste Veranstaltungen:', font=('Helvetica', 18,'bold'), anchor='nw')
    ctx.create_text(600, 350, text='Morgen Auftaktsparty ab 17 Uhr!', font=('Helvetica', 12,'bold'), anchor='nw')
    ctx.create_text(600, 375, text='22. Mai   Schachturnier', font=('Helvetica', 12,'bold'), anchor='nw')
    ctx.create_text(600, 400, text='30. Mai   Mops Geburtstag', font=('Helvetica', 12,'bold'), anchor='nw')
    ctx.create_text(600, 425, text='''14. Juni  Hörsaalkino Special:\n         "Jim Knopf und Lukas\n           der Lokomotivführer"\n       mit Vortrag von Dr. Lohse''', font=('Helvetica', 12,'bold'), anchor='nw')

def load_image(acc, name):
    image = Image.open(image_path.joinpath(f"{name}.png")).resize((40,20))
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


setup(canvas)

s = [
    ("S Adlershof",900193002, True, False, True, 9, 33, 11, 6),
    ("Karl-Ziegler-Str",900000194016, False, True, False, 3, 25, 5, 5),
    ("Magnusstr.",900000194501, False, False, True, 3, 21, 5, 5)
]
stations = []
station_display_offset = 0
for j, sa in enumerate(s):
    if j > 0:
        station_display_offset += stations[j-1].get_dep_list_length() + 1
    stations.append(Station(sa[0],sa[1],sa[2],sa[3], sa[4], sa[5], sa[6], sa[7], sa[8], station_display_offset))

def mainloop():
    for station in stations[:1]:
        station.departure_list()
    root.after(60000, mainloop) #Wait for a minute

root.after(1000, mainloop) # run first time after 1000ms (1s)
root.mainloop()
