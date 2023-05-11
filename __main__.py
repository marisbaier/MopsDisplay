'''
This python script is used to display information on a screen

Author: Maris Baier
'''


import requests
import tkinter as tk
from datetime import datetime

from PIL import ImageTk, Image

global url
url = "https://v5.bvg.transport.rest/stops/900193002/departures?direction=900193001&results=20&suburban=true&tram=false&bus=false&when=in+{0}+minutes"


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
        self.direction = canvas.create_text(230, ypos, text=requestjson['direction'],font=('Helvetica',30,'bold'), anchor='w')
        self.when = canvas.create_text(640, ypos, text=wheninminutes(requestjson),font=('Helvetica',30,'bold'), anchor='w')

    def change(self, image, direction, when):
        canvas.itemconfig(self.image, image = image)
        canvas.itemconfig(self.direction, text=direction)
        canvas.itemconfig(self.when, text=when)


def getDepartures():
    while True:
        try:
            '''
            We try getting the departures in 5, 9, 13 ... minutes. Often times this fails; todo: fix lol
            '''
            response = [requests.get(url.format(i)).json() for i in ["5","9","13","17","21","25","29","33"]]
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
    return int(SbahnJson['when'][14]+SbahnJson['when'][15])-int(datetime.now().strftime("%M"))-60*(int(datetime.now().hour)-int(SbahnJson['when'][12])-10*int(SbahnJson['when'][11]))


### Setup

root = tk.Tk()
root.attributes("-fullscreen", True)
canvas = tk.Canvas()

Empty = ImageTk.PhotoImage(Image.open('MopsDisplay/src/images/Empty.png').resize((1,1)))
imagenames = ['S9', 'S8', 'S85', 'S45', 'S46']
images = {imagename:ImageTk.PhotoImage(Image.open('MopsDisplay/src/images/'+imagename+'.png').resize((80,40))) for imagename in imagenames}

displayedobjects = []

n=0
canvas.create_text(640, 55, text='min', font=('Helvetica',25,'bold'))
canvas.pack(fill=tk.BOTH, expand=True)

def mainloop():
    Sbahnabfahrten = getDepartures()
    if len(Sbahnabfahrten)>len(displayedobjects):
        add = len(displayedobjects)
        #print(len(displayedobjects))
        for i,Sbahn in enumerate(Sbahnabfahrten[len(displayedobjects):-1]):
            i += add
            displayedobjects.append(SbahnObject(Sbahn, ypos=100+i*60))

    for i,displayedobject in enumerate(displayedobjects):

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
    global n
    n+=1
    #print('updated ',n, 'times')
    root.after(1000, mainloop)

root.after(1000, mainloop) # run first time after 1000ms (1s)
root.mainloop()