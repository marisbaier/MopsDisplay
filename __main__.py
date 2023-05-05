import tkinter as tk
from PIL import ImageTk, Image
import requests
from datetime import datetime

root = tk.Tk()
root.attributes("-fullscreen", True)
canvas = tk.Canvas()

imagenames = ['S9', 'S8', 'S85', 'S45', 'S46']
Empty = ImageTk.PhotoImage(Image.open('src/images/Empty.png').resize((1,1)))
sonic = ImageTk.PhotoImage(Image.open('src/images/sonic.png').resize((70,46)))
scary = ImageTk.PhotoImage(Image.open('src/images/scary.png').resize((70,46)))
kermit = ImageTk.PhotoImage(Image.open('src/images/kermit.jfif').resize((70,46)))
images = {}
for imagename in imagenames:
    image = ImageTk.PhotoImage(Image.open('src/images/'+imagename+'.png').resize((80,40)))
    images[imagename]=image

canvas.create_text(640, 55, text='min', font=('Helvetica',25,'bold'))

def displaySBahns(SBahns):
    add = len(displayedobjects)
    for i,Sbahn in enumerate(SBahns):
        i += add
        linename = Sbahn['line']['name']
        lineimage = images[linename]
        displayedobjects.append({'image':
        canvas.create_image(130, 100+i*60, image = lineimage),
        'direction':canvas.create_text(230, 100+i*60, text=Sbahn['direction'],font=('Helvetica',30,'bold'), anchor='w'),
        'when':canvas.create_text(640, 100+i*60, text=int(Sbahn['when'][14]+Sbahn['when'][15])-int(datetime.now().strftime("%M"))-60*(int(datetime.now().hour)-int(Sbahn['when'][12])-10*int(Sbahn['when'][11])),font=('Helvetica',30,'bold'), anchor='w'),
        'hintimage':canvas.create_image(780,100+i*60, image=Empty)
        })
        # , 'delay': canvas.create_text(990,100+i*60, text='+'+str(round(Sbahn['delay']/60,0)),font=('Helvetica',30,'bold'),fill='red')

def getDepartures():
    while True:
        try:
            response = [requests.get("https://v5.bvg.transport.rest/stops/900193002/departures?direction=900193001&results=20&suburban=true&tram=false&bus=false&when=in+{0}+minutes".format(i)).json() for i in ["5","9","13","17","21","25","29","33"]]
        except Exception as errormsg:
            continue
        else:
            Abfahrten=[]
            tripIds=[]
            for i in response:
                for k in i:
                    #print(k['line']['name']+' to '+k['direction'],' in ', k['when'],' id: ', k['tripId'])
                    if k['when'] is not None and k['tripId'] not in tripIds and len(Abfahrten)<9:
                        Abfahrten.append(k)
                        tripIds.append(k['tripId'])
                #print('--------------')
            break
    return Abfahrten

displayedobjects = []

displaySBahns(getDepartures())
n=1

canvas.pack(fill=tk.BOTH, expand=True)

def mainloop():
    Sbahnabfahrten = getDepartures()
    for i,displayedobject in enumerate(displayedobjects):
        if i<len(Sbahnabfahrten):
            Sbahn = Sbahnabfahrten[i]
            linename = Sbahn['line']['name']
            inminutes=int(Sbahn['when'][14]+Sbahn['when'][15])-int(datetime.now().strftime("%M"))-60*(int(datetime.now().hour)-int(Sbahn['when'][12])-10*int(Sbahn['when'][11]))
            canvas.itemconfig(displayedobject['image'], image = images[linename])
            canvas.itemconfig(displayedobject['direction'], text = Sbahn['direction'])
            canvas.itemconfig(displayedobject['when'], text=inminutes)
            if inminutes<11:
                canvas.itemconfig(displayedobject['when'], fill='red')
            else:
                canvas.itemconfig(displayedobject['when'], fill='black')
        else:
            canvas.itemconfig(displayedobject['image'], image = Empty)
            canvas.itemconfig(displayedobject['direction'], text = '')
            canvas.itemconfig(displayedobject['when'], text='')
    if len(Sbahnabfahrten)>len(displayedobjects):
        displaySBahns(Sbahnabfahrten[len(displayedobjects):-1])
    global n
    n+=1
    print('updated ',n, 'times')
    root.after(1000, mainloop)

root.after(1000, mainloop) # run first time after 1000ms (1s)
root.mainloop()




""" if inminutes==10 or inminutes==9:
    canvas.itemconfig(displayedobject['when'], fill='red')
    #canvas.itemconfig(displayedobject['hintimage'], image = sonic)
elif inminutes==11:
    canvas.itemconfig(displayedobject['hintimage'], image = scary)
elif inminutes>11 and inminutes<15:
    canvas.itemconfig(displayedobject['hintimage'], image = kermit)
else:
    canvas.itemconfig(displayedobject['hintimage'], image = Empty) """
""" else:
    canvas.itemconfig(displayedobject['hintimage'], image = kermit) """