import cv
import numpy
import serial
import scipy
import time
import threading
import time
from Tkinter import *
CAMERA_NUM=0
TEMPLATE_MATCH_THRESHOLD=200
CLOSE_THRESHOLD=20000.0
VALUE_THRESHOLD=200
SAT_THRESHOLD=100
HUE_THRESHOLD=25
#image dimensions from webcam are: 640x480
#self.targets={"redBall":((0,160,150),(25,255,255))}
#saturation-how much mixed with white
#value-how much mixed with black
#NOTE: This code is still in development stages and commenting has not been completed.
class VisionSystemApp(Frame,threading.Thread):
    def __init__(self,target):
        #set main instance variables
        self.active=True
        self.target=target
        self.vision=VisionSystem(target)
        self.default=self.vision.targets.copy()
        #call super class methods
        threading.Thread.__init__(self)
        #start the threads and the application mainloop
        #start threads BEFORE mainloop
        self.vision.start()
        self.start()
    def run(self):
        self.master=Tk()
        self.master.title("Ball Tracker System")
        self.master.protocol('WM_DELETE_WINDOW',self.exitMain)
        Frame.__init__(self,self.master)
        self.pack()
        self.createWidgets()
        self.setPresets()
        self.mainloop()
    def createWidgets(self):
        self.mainLabel=Label(self, text="Ball Detection Callibration")
        self.lowerLabel=Label(self, text="HSV Lower Bound")
        self.upperLabel=Label(self, text="HSV Upper Bound")
        self.hueLowerScale=Scale(self,from_=0,to=180, orient=HORIZONTAL,command=self.updateSliders, length=200)
        self.satLowerScale=Scale(self,from_=0,to=255, orient=HORIZONTAL, command=self.updateSliders,length=200)
        self.valueLowerScale=Scale(self,from_=0,to=255,orient=HORIZONTAL, command=self.updateSliders,length=200)
        self.hueUpperScale=Scale(self,from_=0,to=180, orient=HORIZONTAL, command=self.updateSliders,length=200)
        self.satUpperScale=Scale(self,from_=0,to=255, orient=HORIZONTAL, command=self.updateSliders,length=200)
        self.valueUpperScale=Scale(self,from_=0,to=255,orient=HORIZONTAL, command=self.updateSliders,length=200)
        self.defaults=Button(text="Reset To Defaults",command=self.reset)
        self.override=Button(text="Override",command=self.override)
        self.defaults.pack()
        self.override.pack()
        self.mainLabel.pack()
        self.lowerLabel.pack()
        self.hueLowerScale.pack()
        self.satLowerScale.pack()
        self.valueLowerScale.pack()
        self.upperLabel.pack()
        self.hueUpperScale.pack()
        self.satUpperScale.pack()
        self.valueUpperScale.pack()
    def getVisionSystem(self):
        return self.vision
    def override(self):
        self.vision.override=True
    def reset(self):
        (lower,upper)=self.default[self.target]
        self.vision.targets[self.target]=(lower,upper)
        (lH,lS,lV)=lower
        self.hueLowerScale.set(lH)
        self.satLowerScale.set(lS)
        self.valueLowerScale.set(lV)
        (hH,hS,hV)=upper
        self.hueUpperScale.set(hH)
        self.satUpperScale.set(hS)
        self.valueUpperScale.set(hV)
    def setPresets(self):
        lower,upper=self.getBounds()
        (lH,lS,lV)=lower
        self.hueLowerScale.set(lH)
        self.satLowerScale.set(lS)
        self.valueLowerScale.set(lV)
        (hH,hS,hV)=upper
        self.hueUpperScale.set(hH)
        self.satUpperScale.set(hS)
        self.valueUpperScale.set(hV)
    def updateSliders(self,val):
        hueLower=self.hueLowerScale.get()
        satLower=self.satLowerScale.get()
        valLower=self.valueLowerScale.get()
        lower=(hueLower,satLower,valLower)
        self.changeLowerBound(lower)
        hueUpper=self.hueUpperScale.get()
        satUpper=self.satUpperScale.get()
        valUpper=self.valueUpperScale.get()
        upper=(hueUpper,satUpper,valUpper)
        self.changeUpperBound(upper)
    '''def setHueLower(self,val):
    def setHueUpper(self,val):
    def setSatLower(self,val):
    def setSatUpper(self,val):
    def setValLower(self,val):
    def setValUpper(self,val):'''
    def getBounds(self):
        return self.vision.targets[self.vision.target]
    def changeLowerBound(self,lower):
        lowerOld,upper=self.getBounds()
        self.vision.targets[self.vision.target]=(lower,upper)
    def changeUpperBound(self,upper):
        lower,upperOld=self.getBounds()
        self.vision.targets[self.vision.target]=(lower,upper)
    def exitMain(self):
        self.active=False
        self.vision.active=False
        self.vision.join()
        self.master.destroy()
        self.master.quit()
'''Team 12 MASLAB 2013 Vision System API designed to locate certain objects
and command the robot to move towards them'''
class VisionSystem(threading.Thread):
    '''Initialization method that creates the
        camera object and initializes Thread data'''
    def __init__(self,target):
        self.capture = cv.CaptureFromCAM(CAMERA_NUM) #camera object
        self.target=target
        self.active=True
        self.targets={"redBall":((0, 128, 153), (15, 255, 255)),"greenBall":((45, 150, 36), (90, 255, 255))}
        self.calibrated=False
        self.targetLocations={"redBall":None,"greenBall":None,"pyramidTopTemplate":None}
        self.detectionThreshold=TEMPLATE_MATCH_THRESHOLD
        self.run_counter=1
        self.override=False
        #call super class init method and bind to instance
        threading.Thread.__init__(self)
    def smIntegrate(self):
        self.override=False
    def letmerun(self):
        self.run_counter+=1
    def activate(self):
        self.calibrated=True
        self.active=True
        print "calibrated"
    def processImage(self,image):
        #clone image so that we do not tamper with original
        clone=cv.CloneImage(image)
        #blurrs image to reduce color noise
        #cv.CV_BLUR, cv.CV_GAUSSIAN
        blurred=cv.Smooth(clone,clone,cv.CV_GAUSSIAN, 3)
        #converts image to hsv
        hsv=cv.CreateImage(cv.GetSize(clone),8,3)
        cv.CvtColor(clone,hsv,cv.CV_BGR2HSV)
        #threshold image to get only color we want
        thresholded=cv.CreateImage(cv.GetSize(hsv),8,1)
        lowerBound,upperBound=self.targets[self.target]
        cv.InRangeS(hsv,lowerBound,upperBound,thresholded)
        #cv.Erode(thresholded, thresholded, None, 5)
        return thresholded   
    def findMomentsAndArea(self,image):
        mat=cv.GetMat(image)
        moments=cv.Moments(mat)
        area=cv.GetCentralMoment(moments,0,0)
        return (moments,area)
    def findCenterOfMass(self,moments,area):
        if area>0:
            x = int(cv.GetSpatialMoment(moments, 1, 0)/area) 
            y = int(cv.GetSpatialMoment(moments, 0, 1)/area)
            return (x,y)
        else:
            return (None,None)
    def updateCheck(self,current,area):
        (x,y)=current
        if area>self.detectionThreshold and (x,y)!=(None,None):
            return True
        return False
    '''
    This method locates a desired target in an image.
    @param image- an cv image file, ascertained by doing cv.LoadImage("example.jpg")
    @return a cv image file with a box drawn around the located object and a box drawn
    around the center of the image
    '''
    def findTarget(self,image):
         #3 in away=3386655.0 pixel area
        image=cv.CloneImage(image)
        #process image
        processedImage=self.processImage(image)
        moments,area=self.findMomentsAndArea(processedImage)
        (x,y)=self.findCenterOfMass(moments,area)
        #find center of image
        length=10
        centerX,centerY=(int(image.width/float(2)),int(image.height/float(2)))
        center=(centerX-length,centerY-length)
        centerEnd=(centerX+length,centerY+length)
        #find left and right extremems of image
        leftExtreme=(0,int(image.height/float(2)))
        rightExtreme=(image.width,int(image.height/float(2)))
        #place center marker
        cv.Rectangle(image,center,centerEnd,(0,0,255),1,0)
        cv.ShowImage("Ball Tracker Computer Vision",processedImage)
        if self.updateCheck((x,y),area):
            #create target find overlay
            overlay = cv.CreateImage(cv.GetSize(image), 8, 3)
            h=cv.CreateMemStorage(0)
            contours= cv.FindContours(processedImage,h ,cv.CV_RETR_LIST, cv.CV_CHAIN_APPROX_SIMPLE)
            centers=[]
            while contours:
                area1=cv.ContourArea (contours)
                if area1>=TEMPLATE_MATCH_THRESHOLD:
                    moments1 = cv.Moments(contours)
                    #print list(contours)
                    x1 = int(cv.GetSpatialMoment(moments1, 1, 0)/area1) 
                    y1 = int(cv.GetSpatialMoment(moments1, 0, 1)/area1)
                    cv.Circle(overlay, (x1, y1), 2, (0, 255,0), 50) 
                    #cv.DrawContours(image,contours,(0,255,0),(0,255,0),1,20,1)
                    centers.append((area1,(x1,y1)))
                contours=contours.h_next()
            if len(centers)!=0:
                closest=max(centers)
                areat,(x,y)=closest
                #print areat
                xdist=x-image.width/float(2)
                ydist=image.height/float(2)-y
                self.targetLocations[self.target]=((xdist,ydist),(x,y), leftExtreme,rightExtreme,areat)
                cv.Circle(overlay, (x,y), 2, (0, 0, 255), 20)
                cv.Add(image, overlay, image)
                cv.Merge(processedImage, None, None, None, image)
            else:
                self.targetLocations[self.target]=None
        return image
    def getTargetDistFromCenter(self):
        return self.targetLocations[self.target]
    def isClose(self):
        sample=self.targetLocations[self.target]
        if sample==None:
            return False
        else:
            (xDiff,yDiff),(xAbs,yAbs), left,right,area=sample
            (x1,y1)=left
            #print  (xAbs,yAbs)
            #print  (x1,y1)
            if area>=CLOSE_THRESHOLD or yAbs>=(y1/float(2)):
                #print "isClose"
                return True
            else:
                return False
    def changeTarget(self,target):
        self.target=target
        image=cv.QueryFrame(self.capture)
        self.calibrate(image)
    def stop(self):
        self.active=False
        print "Stopping Vision System"
    def run(self):
        print "Starting Vision System"
        if self.capture=="None":
            self.stop()
            return "Camera Init Failed!"
        while self.active:
            if self.run_counter>=1 or self.override:
                #print self.targets[self.target]
                #print self.getTargetDistFromCenter()
                image=cv.QueryFrame(self.capture)
                #print "captured image"
                #print time.time()
                image1=self.findTarget(image)
                #print "found targets"
                cv.ShowImage('Ball Tracker Original',image)
                cv.ShowImage('Ball Tracker Processed',image1)
                if not self.override:
                    self.run_counter-=1
                cv.WaitKey(1)
        print "Stopping Vision System"
        #destroy capture 
        del(self.capture)
        cv.DestroyWindow("Tracker")

if __name__=="__main__":
    t=VisionSystemApp("redBall")

