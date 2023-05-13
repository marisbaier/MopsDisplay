'''
This python script is used to display information on a screen:)

Author: Maris Baier
'''

import os
import re
import requests
import tkinter as tk
from datetime import datetime

from PIL import ImageTk, Image

class SbahnObject:
    def __init__(self, requestjson, ypos):
        '''
        When an S-Bahn object is created, it checks for a correspanding lineimage stored. If there's none, it shows an empty image.
        It then creates text (direction and departure in min).
        '''
        try:
            lineimage = images[requestjson['line']['name']]
        except:
            lineimage = Empty
        self.image = canvas.create_image(130, ypos, image = lineimage)

        direct = requestjson['direction']
        if len(direct) > 15:
            direct = direct[0:15] + "..."
            print(direct)

        self.whenInt = wheninminutes(requestjson)

        self.direction = canvas.create_text(170, ypos, text=direct,font=('Helvetica',20,'bold'), anchor='w')
        self.when = canvas.create_text(480, ypos, text=self.whenInt,font=('Helvetica',20,'bold'), anchor='w')

    def change(self, image, direction, when):
        canvas.itemconfig(self.image, image = image)
        canvas.itemconfig(self.direction, text=direction)
        canvas.itemconfig(self.when, text=when)

class station:
    def __init__(self, name, id, sBahn, Tram, Bus, startFrom=5, upTo=33, distance=11, maxDepatures=6, offset=0):
        self.name = name
        self.id = id
        self.sBahn = sBahn
        self.Tram = Tram
        self.Bus = Bus
        self.offset = offset
        self.startFrom = startFrom
        self.upTo = upTo
        self.distance = distance
        self.maxDepatures = maxDepatures

        self.dObs = []

        self.dObs.append(canvas.create_text(50, 100+self.offset*40, text=self.name,font=('Helvetica',28,'bold'), anchor='w'))
        self.depatureList()


    def depatureList(self):        
        Sbahnabfahrten = getDepartures(self.getUrl(), self.maxDepatures)
        if len(Sbahnabfahrten)>len(self.dObs):
            add = len(self.dObs)
            for i,Sbahn in enumerate(Sbahnabfahrten[len(self.dObs):-1]):
                i += add
                self.dObs.append(SbahnObject(Sbahn, ypos=100+(i+self.offset)*40))

        for i,displayedobject in enumerate(self.dObs[1:]):
            if i<len(Sbahnabfahrten):
                Sbahn = Sbahnabfahrten[i]
                linename = Sbahn['line']['name']
                inminutes = wheninminutes(Sbahn)
                
                direct = Sbahn['direction']
                
                if len(direct) > 15:
                    direct = direct[:15] + "..."


                try:
                    displayedobject.change(images[linename],direct,inminutes)
                except KeyError:
                    if re.match("[0-9]{3}", linename) or Sbahn['line']['adminCode'] == "SEV":
                        displayedobject.change(images['164'],direct,inminutes)
                    else:
                        displayedobject.change(Empty,direct,inminutes)
                if inminutes<self.distance:
                    canvas.itemconfig(displayedobject.when, fill='red')
                else:
                    canvas.itemconfig(displayedobject.when, fill='black')
            else:
                displayedobject.change(Empty,'','')
    
    def getDepListLength(self):
        return len(self.dObs)

    def getUrl(self):
        return f"https://v5.bvg.transport.rest/stops/{self.id}/departures?results=20&suburban={self.sBahn}&tram={self.Tram}&bus={self.Bus}&when=in+{self.startFrom}+minutes&duration={self.upTo}"

def getDepartures(url, maxDepatures):
    while True:
        try:
            response = requests.get(url).json()
        except:
            continue
        else:
            Abfahrten=[]
            tripIds=[]
            for i in response:
                if i['when'] is not None and i['tripId'] not in tripIds and len(Abfahrten)<=maxDepatures:
                    Abfahrten.append(i)
                    tripIds.append(i['tripId'])
            break
    return Abfahrten

def wheninminutes(SbahnJson):
    if int(datetime.now().hour) == 23:
        return int(SbahnJson['when'][14]+SbahnJson['when'][15])-int(datetime.now().strftime("%M"))+60

    return int(SbahnJson['when'][14]+SbahnJson['when'][15])-int(datetime.now().strftime("%M"))-60*(int(datetime.now().hour)-int(SbahnJson['when'][12])-10*int(SbahnJson['when'][11]))

def getImages():
    out = []
    
    for f in os.scandir("MopsDisplay/src/images/"):
        if re.match("S?[0-9]+\.png", f.name):
            out.append(f.name.split(".")[0])

    return out

def setup(canvas, images, HUlogoimage):
    bluecolorbox = canvas.create_rectangle(580, 0, 1200, 800, fill='light blue', outline='light blue')
    HUlogo = canvas.create_image(700, 100, image=HUlogoimage)
    #canvas.create_text(480, 55, text='min', font=('Helvetica',15,'bold'))           # min sign
    canvas.pack(fill=tk.BOTH, expand=True)
    canvas.create_text(600, 300, text='Nächste Veranstaltungen:', font=('Helvetica', 18,'bold'), anchor='nw')
    canvas.create_text(600, 350, text='Morgen Auftaktsparty ab 17 Uhr!', font=('Helvetica', 12,'bold'), anchor='nw')
    canvas.create_text(600, 375, text='22. Mai   Schachturnier', font=('Helvetica', 12,'bold'), anchor='nw')
    canvas.create_text(600, 400, text='30. Mai   Mops Geburtstag', font=('Helvetica', 12,'bold'), anchor='nw')
    canvas.create_text(600, 425, text='''14. Juni  Hörsaalkino Special:\n         "Jim Knopf und Lukas\n           der Lokomotivführer"\n       mit Vortrag von Dr. Lohse''', font=('Helvetica', 12,'bold'), anchor='nw')


### Setup

root = tk.Tk()
root.attributes("-fullscreen", True)
canvas = tk.Canvas()

Empty = ImageTk.PhotoImage(Image.open('MopsDisplay/src/images/Empty.png').resize((1,1)))
HUlogoimage = ImageTk.PhotoImage(Image.open('MopsDisplay/src/images/Huberlin-logo.png').resize((100,100)))
imagenames = getImages()
images = {imagename:ImageTk.PhotoImage(Image.open('MopsDisplay/src/images/'+imagename+'.png').resize((40,20))) for imagename in imagenames}


setup(canvas, images, HUlogoimage)

global stations
s = [("S Adlershof",900193002, True, False, True,9,33, 11, 6), ("Karl-Ziegler-Str",900000194016, False, True, False,3, 25, 5, 5), ("Magnusstr.",900000194501,False, False, True,3, 21, 5, 5)]
stations = []
offset = 0
for j, sa in enumerate(s):
    if j > 0:
        offset += stations[j-1].getDepListLength() + 1
    stations.append(station(sa[0],sa[1],sa[2],sa[3], sa[4], sa[5], sa[6], sa[7], sa[8], offset))

def mainloop():
    for s in stations[:1]:
        s.depatureList()
    root.after(60000, mainloop) #Wait for a minute

root.after(1000, mainloop) # run first time after 1000ms (1s)
root.mainloop()