# Sierra Norstrom
# CMPS 4143-102
# Silly Demo Program I put together for my Python Is Awesome assignment

import tkinter
import time
import os
import random
from tkinter import *
from tkinter import ttk
from tkinter import PhotoImage
from tkinter import messagebox

root = Tk()     # making GUI base

bgcolor = "#AEA1DD"

root.title("Tkinter Demo")     # GUI tab name
root.geometry('700x700')  # GUI default size
root.configure(bg=bgcolor)

counter = 0

# loading in images

honglu = [PhotoImage(file='hongluClass.gif',format = 'gif -index %i' %(i)) for i in range(3)]       # setting image of type gif, along with its frames
ishmael = [PhotoImage(file='ishmaelClass.gif',format = 'gif -index %i' %(i)) for i in range(2)]
donqui = [PhotoImage(file='donquiClass.gif',format = 'gif -index %i' %(i)) for i in range(4)]
stopSign = PhotoImage(file='stop.png')
cat = PhotoImage(file= 'cat.png')

# making functions

def update(ind1):                   # honglu gif
    global current_frame
    frame = honglu[ind1]            # change frame
    label.configure(image = frame, bg = bgcolor)
    ind1 += 1
    if ind1 == 3:
        ind1 = 0
    current_frame = root.after(500, update, ind1) # calls itself to update frames every 500 ms

def update2(ind2):                  # ishmael gif
    global current_frame
    frame = ishmael[ind2]
    label.configure(image = frame, bg = bgcolor)
    ind2 += 1
    if ind2 == 2:
        ind2 = 0
    current_frame = root.after(500, update2, ind2)

def update3(ind3):                  # donqui gif
    global current_frame
    frame = donqui[ind3]
    label.configure(image = frame, bg = bgcolor)
    ind3 += 1
    if ind3 == 4:
        ind3 = 0
    current_frame = root.after(500, update3, ind3)

def updateRandom():
    randX = random.uniform(0, 1)
    randY = random.uniform(0, 1)
    moveLabel.place(relx = randX, rely = randY)
    moveLabelPosX.configure(text = "X: " + str(round(randX, 2)))
    moveLabelPosY.configure(text = "Y: " + str(round(randY, 2)))
    root.after(3000, updateRandom)

# making labels

label = Label(root) # make label in root
countLabel = Label(root, text = counter)
catLabel = Label(root, image = cat)

moveLabel = Label(root, text = "hi")
moveLabelPosX = Label(root, bg = 'white')
moveLabelPosY = Label(root, bg = 'white')

# back to functions

def click1():                           # When 'Hong Lu' Is clicked
    if label.winfo_exists == 1:         # Checking if label already exists, it it does, it gets cleared
        label.destroy()
    btn1.config(state=tkinter.DISABLED)     # disabling use of buttons to remove ability to accidentally stack gifs
    btn2.config(state=tkinter.DISABLED)
    btn3.config(state=tkinter.DISABLED)
    btnStop.config(state=tkinter.NORMAL)    # allow use of 'Stop Gif' button
    
    update(0)                               # calling function to start Hong Lu Gif
    label.pack()                            # setting label into window

def click2():
    if label.winfo_exists == 1:
        label.destroy()
    btn2.config(state=tkinter.DISABLED)
    btn1.config(state=tkinter.DISABLED)
    btn3.config(state=tkinter.DISABLED)
    btnStop.config(state=tkinter.NORMAL)
    
    update2(0)
    label.pack()

def click3():
    if label.winfo_exists == 1:
        label.destroy()
    btn3.config(state=tkinter.DISABLED)
    btn1.config(state=tkinter.DISABLED)
    btn2.config(state=tkinter.DISABLED)
    btnStop.config(state=tkinter.NORMAL)
    
    update3(0)
    label.pack()

def stop():
    root.after_cancel(current_frame)            # stops any currently running 'after' function
    btn1.config(state=tkinter.NORMAL)           # restore use to other buttons
    btn2.config(state=tkinter.NORMAL)
    btn3.config(state=tkinter.NORMAL)
    btnStop.config(state = tkinter.DISABLED)    # re-disable stop button

def bell():
    root.bell()

def popUp():
    msg = messagebox.showinfo("Hi", "This was made by Sierra Norstrom in Python with TKinter\nPython is Awesome!")

def count():
    global counter
    counter += 1
    countLabel.configure(text = counter)

def count2():
    global counter
    counter += 2
    countLabel.configure(text = counter)

# making various buttons

btn1 = Button(root, text = "Hong Lu", command = click1, bg = 'Cyan', font = 'TimesNewRoman')         # start Hong Lu gif
btn2 = Button(root, text = "Ishmael", command = click2, fg = 'Orange', font = 'Georgia')         # start Ishmael gif
btn3 = Button(root, text = "Don Quixote", command = click3, bg = 'Black', fg = 'Yellow', font = 'Comfortaa')     # start Don Quixote gif
btnStop = Button(root, text= "Stop Gif", command = stop, state=tkinter.DISABLED, image=stopSign)        # Stop running gif, can't use if no gif is running
btnBell = Button(root, text = "Click to Ding", command = bell)
btnPop = Button(root, text = "About Program", command = popUp)
btnCount = Button(root, text = "Add 1 to Counter", command = count)
btnCount2 = Button(root, text = "Add 2 to Counter", command = count2)

# putting my buttons and some Labels in to the GUI frame

btn1.place(relx = 0.1, rely = 0.0, anchor = N)      # setting position of Hong Lu Button with .place command
btn2.pack()                                         # setting position of Ishmael Button with .pack
btn3.place(relx = 0.9, rely = 0, anchor = N)
btnStop.pack()
btnBell.pack()
btnPop.pack()

catLabel.place(relx = 0.03, rely = 0.82)
countLabel.place(relx = 0.9, rely = 0.82)
btnCount.place(relx = 0.9, rely = .9, anchor = S)
btnCount2.place(relx = 0.9, rely = .95, anchor = S)

moveLabelPosX.place(relx = .05, rely = 0.5)
moveLabelPosY.place(relx = .05, rely = 0.55)

root.after(1000, updateRandom)

root.mainloop()     # run program, at end++