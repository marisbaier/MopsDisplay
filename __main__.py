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
    def __init__(self, name, id, sBahn, Tram, Bus, upTo, offset=0):
        self.name = name
        self.id = id
        self.sBahn = sBahn
        self.Tram = Tram
        self.Bus = Bus
        self.offset = offset
        self.upTo = upTo

        self.dObs = []

        Sbahnabfahrten = getDepartures(self.getUrl(), self.upTo)
        
        self.dObs.append(canvas.create_text(50, 100+self.offset*40, text=self.name,font=('Helvetica',28,'bold'), anchor='w'))
        for i,Sbahn in enumerate(Sbahnabfahrten[len(self.dObs):-1]):
            i += 1
            self.dObs.append(SbahnObject(Sbahn, ypos=100+(i+self.offset)*40))


    def depatureList(self):        
        Sbahnabfahrten = getDepartures(self.getUrl(), self.upTo)
        if len(Sbahnabfahrten)>len(self.dObs):
            add = len(self.dObs)
            for i,Sbahn in enumerate(Sbahnabfahrten[len(self.dObs):-1]):
                i += add
                self.dObs.append(SbahnObject(Sbahn, ypos=100+(i)*40))

        for i,displayedobject in enumerate(self.dObs):
            if i<len(Sbahnabfahrten):
                Sbahn = Sbahnabfahrten[i]
                linename = Sbahn['line']['name']
                inminutes = wheninminutes(Sbahn)
                displayedobject.change(images[linename],Sbahn['direction'],inminutes)
                if inminutes<11:
                    canvas.itemconfig(displayedobject.when, fill='red')
                else:
                    canvas.itemconfig(displayedobject.when, fill='black')
            else:
                displayedobject.change(Empty,'','')

        return self.dObs
    
    def getDepListLength(self):
        return len(self.dObs)

    def getUrl(self):
        return f"https://v5.bvg.transport.rest/stops/{self.id}/departures?results=20&suburban={self.sBahn}&tram={self.Tram}&bus={self.Bus}&when="+"in+{0}+minutes"


def getDepartures(url, upTo):
    while True:
        try:
            '''
            We try getting the departures in 5, 9, 13 ... minutes. Often times this fails; todo: fix lol
            '''
            response = [requests.get(url.format(str(i))).json() for i in range(5,upTo, 4)]
        except:
            continue
        else:
            Abfahrten=[]
            tripIds=[]
            for i in response:
                for k in i:
                    if k['when'] is not None and k['tripId'] not in tripIds and len(Abfahrten)<9:
                        Abfahrten.append(k)
                        tripIds.append(k['tripId'])
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


### Setup

root = tk.Tk()
root.attributes("-fullscreen", True)
canvas = tk.Canvas()

Empty = ImageTk.PhotoImage(Image.open('MopsDisplay/src/images/Empty.png').resize((1,1)))
HUlogoimage = ImageTk.PhotoImage(Image.open('MopsDisplay/src/images/Huberlin-logo.png').resize((100,100)))
imagenames = getImages()
images = {imagename:ImageTk.PhotoImage(Image.open('MopsDisplay/src/images/'+imagename+'.png').resize((40,20))) for imagename in imagenames}

displayedobjects = []

n=0
canvas.create_text(480, 55, text='min', font=('Helvetica',15,'bold'))           # min sign
canvas.pack(fill=tk.BOTH, expand=True)
bluecolorbox = canvas.create_rectangle(580, 0, 1200, 800, fill='light blue', outline='light blue')
HUlogo = canvas.create_image(700, 100, image=HUlogoimage)
canvas.create_text(600, 300, text='Nächste Veranstaltungen:', font=('Helvetica', 18,'bold'), anchor='nw')
canvas.create_text(600, 350, text='Morgen Auftaktsparty ab 17 Uhr!', font=('Helvetica', 12,'bold'), anchor='nw')
canvas.create_text(600, 375, text='22. Mai   Schachturnier', font=('Helvetica', 12,'bold'), anchor='nw')
canvas.create_text(600, 400, text='30. Mai   Mops Geburtstag', font=('Helvetica', 12,'bold'), anchor='nw')
canvas.create_text(600, 425, text='''14. Juni  Hörsaalkino Special:\n         "Jim Knopf und Lukas\n           der Lokomotivführer"\n       mit Vortrag von Dr. Lohse''', font=('Helvetica', 12,'bold'), anchor='nw')

global stations
s = [("Adlershof",900193002, True, False, False,60), ("Karl-Ziegler-Str",900000194016, False, True, False, 25), ("Magnusstr.",900000194501,False, False, True, 21)]
stations = []
offset = 0
for j, sa in enumerate(s):
    if j > 0:
        offset += stations[j-1].getDepListLength() + 1
    stations.append(station(sa[0],sa[1],sa[2],sa[3], sa[4], sa[5], offset))

def mainloop():
    for s in stations[:1]:
        s.depatureList()
    #print('updated ',n, 'times')
    root.after(1000, mainloop)

root.after(1000, mainloop) # run first time after 1000ms (1s)
root.mainloop()