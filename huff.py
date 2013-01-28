import cv2
import cv
import numpy as np
import serial
import scipy
import time
import threading
import time
import math
import copy
from Tkinter import *

class Huff:
    def __init__(self,filename,g="output.jpg"):
#        self.image=cv2.imread(filename)
        print time.time()
        self.image=cv.LoadImage(filename)
        self.g=g
        print self.image.__class__.__name__
        downSampledImage=cv.CreateImage((408,230),8,3)
        cv.Resize(self.image,downSampledImage)
        self.image=downSampledImage
        #cv2.resize
        #self.image=cv.fromarray(self.image)
        self.override=False
        self.c1=50
        self.c2=200
        self.ap=3
        self.rh=1
        self.deg=.5
        self.th=2
        self.min_l=70
        self.max_d=20
        self.lines=[]
        self.gray=None
        self.bw=None
        self.edges=None
        self.bwt=90
        cv.Smooth(self.image,self.image,cv.CV_GAUSSIAN, 3,3)
        self.image2=np.asarray(cv.CloneImage(self.image)[:,:])
    def huff(self):
        print "resetting image 2"
        time1=time.time()
        self.image2=np.asarray(cv.CloneImage(self.image)[:,:])
        print "seconds: ",time.time()-time1
        self.gray = cv2.cvtColor(self.image2, cv2.COLOR_BGR2GRAY)
        print "seconds: ",time.time()-time1
        if not self.override:
            (thresh,self.bw) = cv2.threshold(self.gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            print "threshold: ",thresh
        else:
            self.bw = cv2.threshold(self.gray, self.bwt, 255, cv2.THRESH_BINARY)[1]
        print "seconds: ",time.time()-time1
        cv2.imwrite("bw.jpg",self.bw)
        #thresh = 127
        #im_bw = cv2.threshold(im_gray, thresh, 255, cv2.THRESH_BINARY)[1]
        self.edges = cv2.Canny(self.bw, self.c1, self.c2,apertureSize=self.ap)
        print "seconds: ",time.time()-time1
        #cv2.imwrite("wall3.jpg",self.edges)
#        cv.ShowImage('Edges',cv.fromarray(edges))
        #print (self.edges, self.rh, math.pi/180*self.deg\
#                                , self.th, None, self.min_l, self.max_d)
        #this takes ~.035 seconds
        self.lines = cv2.HoughLinesP(self.edges, self.rh, math.pi/180*self.deg\
                                , self.th, None, self.min_l, self.max_d)
        #emptyImage=cv.CreateImage((480,240),8,3)
        #whole thing takes ~.10-.11 seconds
        print "seconds: ",time.time()-time1
        if self.lines==None:
            self.lines=[[]]
        print "Number of lines:", len(self.lines[0])
        for line in self.lines[0]:
            pt1 = (line[0],line[1])
            pt2 = (line[2],line[3])
            cv2.line(self.image2, pt1, pt2, (0,0,255), 3)
        cv2.imwrite(self.g, self.image2)
        return self.lines
    def draw(self):
        print "Updating image, please wait..."
        cv2.imshow('edges',self.image2)
        print "Updated image"
        
class GUI(Frame,threading.Thread):
    def __init__(self):
        f=raw_input("Input file: ")
        g=raw_input("Output file: ")
        #set main instance variables
        self.active=True
        self.h=Huff(f,g)
        #call super class methods
        threading.Thread.__init__(self)
        #start the threads and the application mainloop
        #start threads BEFORE mainloop
        self.start()
    def run(self):
        self.buildGUI()
    def buildGUI(self):
        self.master=Tk()
        self.master.title("Edge detection")
        self.master.protocol('WM_DELETE_WINDOW',self.stop)
        Frame.__init__(self,self.master)
        self.pack()
        self.createWidgets()
        self.setPresets()
        self.mainloop()
    def createWidgets(self):
        self.c1Label=Label(self, text="Canny lower bound")
        self.c2Label=Label(self, text="Canny upper bound")
        self.apLabel=Label(self, text="Aperture")
        self.rhLabel=Label(self, text="Rho")
        self.degLabel=Label(self, text="Degrees")
        self.thLabel=Label(self, text="Threshold")
        self.min_lLabel=Label(self, text="min line length")
        self.max_dLabel=Label(self, text="max line distance")
        self.bwLabel=Label(self, text="black/white threshold")
        self.c1s=Scale(self,from_=0,to=250, orient=HORIZONTAL,command=self.updateSliders, length=250)
        self.c2s=Scale(self,from_=0,to=250, orient=HORIZONTAL,command=self.updateSliders, length=250)
        self.aps=Scale(self,from_=0,to=10, orient=HORIZONTAL, command=self.updateSliders,length=250)
        self.rhs=Scale(self,from_=0,to=5, resolution=.5,orient=HORIZONTAL, command=self.updateSliders,length=250)
        self.degs=Scale(self,from_=0,to=90, resolution=.5, orient=HORIZONTAL, command=self.updateSliders,length=250)
        self.ths=Scale(self,from_=0,to=5, resolution=1,orient=HORIZONTAL, command=self.updateSliders,length=250)
        self.min_ls=Scale(self,from_=0,to=500,resolution=10,orient=HORIZONTAL, command=self.updateSliders,length=250)
        self.max_ds=Scale(self,from_=0,to=50,resolution=5,orient=HORIZONTAL, command=self.updateSliders,length=250)
        self.overrideb=Button(text="Override bw thresholding",command=self.override)
        self.autob=Button(text="Auto bw thresholding",command=self.auto)
        self.bws=Scale(self,from_=0,to=255, orient=HORIZONTAL,command=self.updateSliders, length=250)
        self.c1Label.pack()
        self.c1s.pack()
        self.c2Label.pack()
        self.c2s.pack()
        self.apLabel.pack()
        self.aps.pack()
        self.rhLabel.pack()
        self.rhs.pack()
        self.degLabel.pack()
        self.degs.pack()
        self.thLabel.pack()
        self.ths.pack()
        self.min_lLabel.pack()
        self.min_ls.pack()
        self.max_dLabel.pack()
        self.max_ds.pack()
        self.autob.pack()
        self.overrideb.pack()
        self.bwLabel.pack()
        self.bws.pack()
    def getHuff(self):
        return self.h
    def setPresets(self):
        self.c1s.set(self.h.c1)
        self.c2s.set(self.h.c2)
        self.aps.set(self.h.ap)
        self.rhs.set(self.h.rh)
        self.degs.set(self.h.deg)
        self.ths.set(self.h.th)
        self.min_ls.set(self.h.min_l)
        self.max_ds.set(self.h.max_d)
        self.bws.set(self.h.bwt)
    def updateSliders(self,val):
        self.h.c1=self.c1s.get()
        self.h.c2=self.c2s.get()
        self.h.ap=self.aps.get()
        self.h.rh=self.rhs.get()
        self.h.deg=self.degs.get()
        self.h.th=self.ths.get()
        self.h.min_l=self.min_ls.get()
        self.h.max_d=self.max_ds.get()
        self.h.bwt=self.bws.get()
        self.h.huff()
        self.h.draw()
    def stop(self):
        self.active=False
        self.master.quit()
    def override(self):
        self.h.override=True
        self.h.huff()
        self.h.draw()
    def auto(self):
        self.h.override=False
        self.h.huff()
        self.h.draw()

if __name__=="__main__":
    GUI()
#h=Huff("wall.jpg")
#h.huff()
