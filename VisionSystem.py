import cv
import numpy as np
import serial
import scipy
import time
import threading
import time
import math
from Tkinter import *
TEMPLATE_MATCH_THRESHOLD=200/2.7 #depends on image size
CLOSE_THRESHOLD=20000.0/2.7
VALUE_THRESHOLD=200
SAT_THRESHOLD=100
HUE_THRESHOLD=25
#image dimensions from webcam are: 640x480
#self.targets={"redBall":((0,160,150),(25,255,255))}
#saturation-how much mixed with white
#value-how much mixed with black
#NOTE: This code is still in development stages and commenting has not been completed.
'''
GUI for working with the Vision System. With this GUI you are easily able to fine tune the HSV ranges for the desired
color of the object you want to detect using a slider based calibration mechanism.
'''
class VisionSystemApp(Frame,threading.Thread):
    def __init__(self):
        #set main instance variables
        self.active=True
        self.vision=VisionSystem()
        self.default=self.vision.targetColorProfiles.copy()
        self.selectedTarget="redBall"
        #call super class methods
        threading.Thread.__init__(self)
        #start the threads and the application mainloop
        #start threads BEFORE mainloop
        self.vision.start()
        self.start()
    def run(self):
        self.buildGUI()
    def buildGUI(self):
        self.master=Tk()
        self.master.title("Ball Tracker System")
        self.master.protocol('WM_DELETE_WINDOW',self.stop)
        Frame.__init__(self,self.master)
        self.pack()
        self.createWidgets()
        self.setPresets()
        self.mainloop()
    def createWidgets(self):
        self.mainLabel=Label(self, text="Ball Detection Callibration")
        self.lowerLabel=Label(self, text="HSV Lower Bound")
        self.upperLabel=Label(self, text="HSV Upper Bound")
        self.targetLabel1=Label(self,text="Choose Target 1")
        self.targetLabel2=Label(self,text="Choose Target 2")
        self.cameraLabel=Label(self,text="Change Camera Number")
        self.targetString1 = StringVar(self.master)
        self.targetString1.set("redBall")
        self.selectTarget1=OptionMenu(self, self.targetString1, "redBall","greenBall","blueWall","yellowWall","purpleWall","yellowWall2",command=self.switchTargetScales)
        self.cameraString=StringVar(self.master)
        self.cameraString.set("0")
        self.selectCamera=OptionMenu(self, self.cameraString,"0","1","2",command=self.changeCameraNumber)
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
        self.cameraLabel.pack()
        self.selectCamera.pack()
        self.targetLabel1.pack()
        self.selectTarget1.pack()
        self.lowerLabel.pack()
        self.hueLowerScale.pack()
        self.satLowerScale.pack()
        self.valueLowerScale.pack()
        self.upperLabel.pack()
        self.hueUpperScale.pack()
        self.satUpperScale.pack()
        self.valueUpperScale.pack()
    def changeCameraNumber(self,val):
        self.vision.changeCameraNumber(val)
    def switchTargetScales(self,val):
        targetStr=val
        self.vision.removeTarget(self.selectedTarget)
        self.selectedTarget=targetStr
        self.vision.addTarget(targetStr)
        self.reset()
    def getVisionSystem(self):
        return self.vision
    def override(self):
        self.vision.override=True
    def reset(self):
        (lower,upper)=self.default[self.selectedTarget]
        self.vision.targetColorProfiles[self.selectedTarget]=(lower,upper)
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
        return self.vision.targetColorProfiles[self.selectedTarget]
    def changeLowerBound(self,lower):
        lowerOld,upper=self.getBounds()
        self.vision.targetColorProfiles[self.selectedTarget]=(lower,upper)
    def changeUpperBound(self,upper):
        lower,upperOld=self.getBounds()
        self.vision.targetColorProfiles[self.selectedTarget]=(lower,upper)
    def stop(self):
        self.active=False
        self.vision.active=False
        self.vision.join()
        self.master.quit()
'''Team 12 MASLAB 2013 Vision System API designed to locate certain objects
and command the robot to move towards them'''
class VisionSystem(threading.Thread):
    '''Initialization method that creates the
        camera object and initializes Thread data'''
    def __init__(self):
        self.capture = cv.CaptureFromCAM(0) #camera object
        self.targets=[]
        self.active=True
        self.targetColorProfiles={"redBall":((0, 128, 153), (15, 255, 255)),"greenBall":((45, 150, 36), (90, 255, 255)),
                      "blueWall":((103, 141, 94), (115, 255, 255)),"yellowWall":((29, 150, 36), (64, 255, 255)),
                                  "purpleWall":((119, 117, 52), (129, 255, 255)),"yellowWall2":((26, 53,117), (32, 255, 255))}
        self.targetShapeProfiles={"redBall":self.detectCircle,"greenBall":self.detectCircle,
                      "blueWall":self.detectRectangle,"yellowWall":self.detectRectangle,"purpleWall":self.detectRectangle,
                                  "yellowWall2":self.detectRectangle}
        self.calibrated=False
        self.targetLocations={"redBall":None,"greenBall":None,"blueWall":None,"yellowWall":None,"purpleWall":None,"yellowWall2":None}
        self.bestTargetOverall=None #will be (target,distFromCenter,absolute coordinates,area)
        self.detectionThreshold=TEMPLATE_MATCH_THRESHOLD
        self.run_counter=1
        self.override=False
        self.pause=False
        self.imageParams=None
        self.lock=threading.Lock()
        #call super class init method and bind to instance
        threading.Thread.__init__(self)
        print "Tracking no targets!"
    def changeCameraNumber(self,index):
        with self.lock:
            self.pause=True
            del(self.capture)
            try:
                index=int(index)
                self.capture=cv.CaptureFromCAM(index)
            except:
                print "Invalid camera number!"
            self.pause=False
    def smIntegrate(self):
        self.override=False
    def letmerun(self):
        self.run_counter+=1
    def activate(self):
        self.calibrated=True
        self.active=True
        print "calibrated"
    def addTarget(self,targetStr):
        if targetStr in self.targetColorProfiles:
            self.targets.append(targetStr)
        else:
            print "Target: "+str(targetStr)+" is not a valid target!"
    def removeTarget(self,targetStr):
        if targetStr in self.targets:
            self.targets.remove(targetStr)
        else:
            print "Target: "+str(targetStr)+" is currently not being tracked!"
    def clearTargets(self):
        self.targets=[]
        print "Targets have been cleared!"
    def getTargetDistFromCenter(self,target="all"):
        if target in self.targetLocations:
            return self.targetLocations[target]
        else:
            if target=="all":
                return self.bestTargetOverall
        
    def isClose(self,target="all"):
        if target in self.targetLocations:
            sample=self.targetLocations[target]
        else:
            if target=="all":
                sample=self.bestTargetOverall
        if sample==None:
            return False
        else:
            targetStr,(xDiff,yDiff),(xAbs,yAbs),area=sample
            imageData=self.imageParams
            if imageData==None:
                return False
            (x1,y1),center,leftExt,rightExt=imageData
            if area>=CLOSE_THRESHOLD or yAbs>=(y1/float(2)):
                #print "isClose"
                return True
            else:
                return False
    def processImage(self,image):
        #clone image so that we do not tamper with original
        clone=cv.CloneImage(image)
        #blurrs image to reduce color noise
        #cv.CV_BLUR, cv.CV_GAUSSIAN
        blurred=cv.Smooth(clone,clone,cv.CV_GAUSSIAN, 3,3)
        #converts image to hsv
        hsv=cv.CreateImage(cv.GetSize(clone),8,3)
        cv.CvtColor(clone,hsv,cv.CV_BGR2HSV)
        #cv.Erode(thresholded, thresholded, None, 5)
        return hsv
    def processImagePhase2(self,processedImage,colorProfile):
        lowerBound,upperBound=colorProfile
        #threshold image to get only color we want
        thresholded=cv.CreateImage(cv.GetSize(processedImage),8,1)
        cv.InRangeS(processedImage,lowerBound,upperBound,thresholded)
        return thresholded
    def findTargets(self,image):
        initialProcessedImage=self.processImage(image)
        #remove top of image
        targetMain="blueWall"
        (data,processedImagePhase2)=self.findTarget(initialProcessedImage,targetMain)
        ignoreRegion=None
        if data!=None:
            ((xdist,ydist),(x,y),areat,centers)=data
            ignoreRegion=y
        targetLocations=[]
        processedImages=[]
        maxTargetArea=0
        maxTargetY=0
        maxTargetLocation=None
        if len(self.targets)!=0:
            for target in self.targets:
                (targetsData,processedImagePhase2)=self.findTarget(initialProcessedImage,target,ignoreRegion)
                processedImages.append(processedImagePhase2)
                if targetsData==None:
                    continue
                (xdist,ydist),(x,y),areat,centers=targetsData
                if areat>maxTargetArea and y>maxTargetY:
                    maxTargetArea=areat
                    maxTargetY=y
                    maxTargetLocation=(target,(xdist,ydist),(x,y),areat)
                targetLocations.extend(centers)
            self.bestTargetOverall=maxTargetLocation
        else:
            (targetsData,processedImagePhase2)= self.findTarget(initialProcessedImage,None)
            processedImages.append(processedImagePhase2)
        self.renderImages(image,processedImages,targetLocations)
    def renderImages(self,original,processedImages,allTargetLocations):
        #cv.ShowImage('Ball Tracker Original',original)
        ((width,height),(center,centerEnd),leftExtreme,rightExtreme)=self.findCenterOfImageAndExtremes(original)
        cv.Rectangle(original,center,centerEnd,(0,0,255),1,0)
        overlay = cv.CloneImage(original)
        completeProcessedImage=processedImages[0]
        for i in range(1,len(processedImages)):
            cv.Add(completeProcessedImage,processedImages[i],completeProcessedImage)
        cv.ShowImage("Ball Tracker Computer Vision",completeProcessedImage)
        for targetLocation in allTargetLocations:
            (area1,(x1,y1))=targetLocation
            cv.Circle(overlay, (x1, y1), 2, (0, 255,0), 50)
        if self.bestTargetOverall!=None:
            (target,(xdist,ydist),(x,y),areat)=self.bestTargetOverall
            cv.Circle(overlay, (x,y), 2, (0, 0, 255), 20)
        cv.Add(original, overlay, original)
        #cv.Merge(completeProcessedImage, None, None, None, original)
        cv.ShowImage('Ball Tracker Processed',original)
    def detectCircle(self,processedImage,contours,area):
        return True
    def detectRectangle(self,processedImage,contours,area):
        return True
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
    def findCenterOfImageAndExtremes(self,image):
        #find center of image
        length=10
        centerX,centerY=(int(image.width/float(2)),int(image.height/float(2)))
        center=(centerX-length,centerY-length)
        centerEnd=(centerX+length,centerY+length)
        #find left and right extremems of image
        leftExtreme=(0,int(image.height/float(2)))
        rightExtreme=(image.width,int(image.height/float(2)))
        return ((image.width,image.height),(center,centerEnd),leftExtreme,rightExtreme)
    def findTarget(self,processedImage,target,ignoreRegion=None):
         #3 in away=3386655.0 pixel area
        image=cv.CloneImage(processedImage)
        #process image
        if target==None or target not in self.targetColorProfiles:
            colorProfile=((256,256,256),(256,256,256))
        else:
            colorProfile=self.targetColorProfiles[target]
        processedImagePhase2=self.processImagePhase2(processedImage,colorProfile)
        moments,area=self.findMomentsAndArea(processedImagePhase2)
        (x,y)=self.findCenterOfMass(moments,area)
        data=(None,processedImagePhase2)
        savedData=None
        if self.updateCheck((x,y),area):
            #create target find overlay
            h=cv.CreateMemStorage(0)
            cloneForContour=cv.CloneImage(processedImagePhase2)
            contours= cv.FindContours(cloneForContour,h ,cv.CV_RETR_LIST, cv.CV_CHAIN_APPROX_SIMPLE)
            centers=[]
            while contours:
                area1=cv.ContourArea (contours)
                if area1>=TEMPLATE_MATCH_THRESHOLD:
                    #see if found contour matches shape description
                    objectMatch=self.targetShapeProfiles[target](processedImagePhase2,contours,area1)
                    if objectMatch:
                        moments1 = cv.Moments(contours)
                        #print list(contours)
                        x1 = int(cv.GetSpatialMoment(moments1, 1, 0)/area1) 
                        y1 = int(cv.GetSpatialMoment(moments1, 0, 1)/area1)
                        #cv.DrawContours(image,contours,(0,255,0),(0,255,0),1,20,1)
                        #ignore the object detected if a blue wall is detected and the the object is above the wall
                        #helps prevent detecting objects from audience
                        #ignore region is essentially the region above the horizontal line that represents the y coordinate
                        #of the center of mass of the blue wall detected
                        if ignoreRegion!=None and target!="blueWall":
                            if y1>ignoreRegion:
                                centers.append((area1,(x1,y1)))
                        else:
                            centers.append((area1,(x1,y1)))
                contours=contours.h_next()
            if len(centers)!=0:
                closest=max(centers)
                areat,(x,y)=closest
                #print areat
                xdist=x-image.width/float(2)
                ydist=image.height/float(2)-y
                data=(((xdist,ydist),(x,y),areat,centers),processedImagePhase2)
                savedData=(target,(xdist,ydist),(x,y),areat)
        self.targetLocations[target]=savedData
        return data
    def stop(self):
        self.active=False
        print "Stopping Vision System"
    def run(self):
        print "Starting Vision System"
        if self.capture=="None":
            self.stop()
            return "Camera Init Failed!"
        while self.active:
            if self.run_counter>=1 or self.override and not self.pause:
                #print self.targets[self.target]
                #print self.getTargetDistFromCenter()
                image=cv.QueryFrame(self.capture)
                downSampledImage=cv.CreateImage((480,240),8,3)
                cv.Resize(image,downSampledImage)
                #print "captured image"
                #print time.time()
                self.imageParams=self.findCenterOfImageAndExtremes(downSampledImage)
                self.findTargets(downSampledImage)
                #print "found targets"
                if not self.override:
                    self.run_counter-=1
                cv.WaitKey(1)
        print "Stopping Vision System"
        #destroy capture 
        del(self.capture)
        cv.DestroyWindow("Tracker")

if __name__=="__main__":
    t=VisionSystemApp()

