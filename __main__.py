import tkinter as tk
from PIL import ImageTk, Image
import requests
from datetime import datetime

class SbahnObject:
    def __init__(self, lineimage, direction, when, hintimage, ypos):
        self.image = canvas.create_image(130, ypos, image = lineimage)
        self.direction = canvas.create_text(230, ypos, text=direction,font=('Helvetica',30,'bold'), anchor='w')
        self.when = canvas.create_text(640, ypos, text=when,font=('Helvetica',30,'bold'), anchor='w')
        self.hintimage = canvas.create_image(780,ypos, image=hintimage)
    def change(self, image, direction, when):
        canvas.itemconfig(self.image, image = image)
        canvas.itemconfig(self.direction, text=direction)
        canvas.itemconfig(self.when, text=when)

def getDepartures():
    while True:
        try:
            response = [requests.get("https://v5.bvg.transport.rest/stops/900193002/departures?direction=900193001&results=20&suburban=true&tram=false&bus=false&when=in+{0}+minutes".format(i)).json() for i in ["5","9","13","17","21","25","29","33"]]
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

imagenames = ['S9', 'S8', 'S85', 'S45', 'S46']
Empty = ImageTk.PhotoImage(Image.open('src/images/Empty.png').resize((1,1)))
images = {imagename:ImageTk.PhotoImage(Image.open('src/images/'+imagename+'.png').resize((80,40))) for imagename in imagenames}

displayedobjects = []

n=0
canvas.create_text(640, 55, text='min', font=('Helvetica',25,'bold'))
canvas.pack(fill=tk.BOTH, expand=True)

def mainloop():
    Sbahnabfahrten = getDepartures()
    if len(Sbahnabfahrten)>len(displayedobjects):
        add = len(displayedobjects)
        print(len(displayedobjects))
        for i,Sbahn in enumerate(Sbahnabfahrten[len(displayedobjects):-1]):
            i += add
            linename = Sbahn['line']['name']
            lineimage = images[linename]
            wheninminutes = wheninminutes(Sbahn)
            displayedobjects.append(SbahnObject(lineimage,Sbahn['direction'],wheninminutes,hintimage=Empty,ypos=100+i*60))

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
    print('updated ',n, 'times')
    root.after(1000, mainloop)

root.after(1000, mainloop) # run first time after 1000ms (1s)
root.mainloop()