import cv
import cv2
import numpy as np
import serial
import scipy
import time
import threading
from multiprocessing import Process,Pipe,Queue
import time
import math
import copy
import json
from Tkinter import *
TEMPLATE_MATCH_THRESHOLD=200/2.7 #depends on image size
CLOSE_THRESHOLD=20000.0/2.7
VALUE_THRESHOLD=200
SAT_THRESHOLD=100
HUE_THRESHOLD=25
MAXRANGE=50
#image dimensions from webcam are: 640x480
#self.targets={"redBall":((0,160,150),(25,255,255))}
#saturation-how much mixed with white
#value-how much mixed with black
#NOTE: This code is still in development stages and commenting has not been completed.
class VisionSystemWrapper:
    def __init__(self):
        self.cmdQueue=Queue(1000)
        self.dataQueue=Queue(1000)
        self.VisionSystem=VisionSystemApp(self.cmdQueue,self.dataQueue)
    def addTarget(self,targetStr):
        cmd=("addTarget",(targetStr,))
        self.cmdQueue.put(cmd)
    def removeTarget(self,targetStr):
        cmd=("removeTarget",(targetStr,))
        self.cmdQueue.put(cmd)
    def clearTargets(self):
        cmd=("clearTargets",())
        self.cmdQueue.put(cmd)
    def getTargetDistFromCenter(self,target="all"):
        cmd=("getTargetDistFromCenter",(target,))
        self.cmdQueue.put(cmd)
        return self.dataQueue.get()
    def isClose(self,target="all"):
        cmd=("isClose",(target,))
        self.cmdQueue.put(cmd)
        return self.dataQueue.get()
    def getWallCoordinates(self):
        cmd=("getWallCoordinates",())
        self.cmdQueue.put(cmd)
        return self.dataQueue.get()
    def activate(self):
        cmd=("activate",())
        self.cmdQueue.put(cmd)
    def smIntegrate(self):
        cmd=("smIntegrate",())
        self.cmdQueue.put(cmd)
    def changeCameraNumber(self,index):
        cmd=("changeCameraNumber",(index,))
        self.cmdQueue.put(cmd)
    def stop(self):
        cmd=("stop",())
        self.cmdQueue.put(cmd)
'''
GUI for working with the Vision System. With this GUI you are easily able to fine tune the HSV ranges for the desired
color of the object you want to detect using a slider based calibration mechanism.
'''
class VisionSystemApp(Frame,Process):
    def __init__(self,cmdQueue,dataQueue):
         #call super class methods
        Process.__init__(self)
        #set main instance variables
        self.active=True
        self.selectedTarget="redBall"
        #start the threads and the application mainloop
        #start threads BEFORE mainloop
        self.cmdQueue=cmdQueue
        self.dataQueue=dataQueue
        self.start()
    def run(self):
        self.vision=VisionSystem(self.cmdQueue,self.dataQueue)
        self.vision.start()
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
        self.selectTarget1=OptionMenu(self, self.targetString1, "redBall","greenBall","blueWall","yellowWall","purpleWall",
                                      "yellowWall2","cyanButton",command=self.switchTargetScales)
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
        return self.vision.getData()
    def override(self):
        self.vision.override=True
    def reset(self):
        (lower,upper)=self.vision.getDefaultMainColorProfile(self.selectedTarget)
        self.vision.setMainColorProfile(self.selectedTarget,(lower,upper))
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
        return self.vision.getMainColorProfile(self.selectedTarget)
    def changeLowerBound(self,lower):
        lowerOld,upper=self.getBounds()
        self.vision.setMainColorProfile(self.selectedTarget,(lower,upper))
    def changeUpperBound(self,upper):
        lower,upperOld=self.getBounds()
        self.vision.setMainColorProfile(self.selectedTarget,(lower,upper))
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
    def __init__(self,cmdQueue,dataQueue):
        self.capture = cv.CaptureFromCAM(0) #camera object
        self.targets=[]
        self.ballTargets=["redBall","greenBall"]
        self.wallTargets=["blueWall","purpleWall"]
        self.wallCoordinates=[]
        self.active=True
        self.targetColorProfiles={"redBall":[((0, 147, 73), (15, 255, 255)),((165, 58, 36), (180, 255, 255))],"greenBall":[((45, 150, 36), (90, 255, 255))],
                      "blueWall":[((103, 141, 94), (115, 255, 255))],"yellowWall":[((29, 150, 36), (64, 255, 255))],
                                  "purpleWall":[((119, 117, 52), (129, 255, 255))],"yellowWall2":[((26, 53,117), (32, 255, 255))],
                                  "cyanButton":[((95,176,115),(108,255,255))]}
        self.targetShapeProfiles={"redBall":self.detectCircle,"greenBall":self.detectCircle,
                      "blueWall":self.detectRectangle,"yellowWall":self.detectRectangle,"purpleWall":self.detectRectangle,
                                  "yellowWall2":self.detectRectangle,"cyanButton":self.detectRectangle}
        self.edgeDetectionProfiles={"main":(50,200,3,1,.5,2,70,20,90)} #c1,c2,ap,rh,deg,th,min_l,max_d,bwt
        self.default= copy.deepcopy(self.targetColorProfiles)
        self.defaultEdgeDetectionProfiles= copy.deepcopy(self.edgeDetectionProfiles)
        self.targetLocations={"redBall":None,"greenBall":None,"blueWall":None,"yellowWall":None,"purpleWall":None,
                              "yellowWall2":None,"cyanButton":None}
        self.bestTargetOverall=None #will be (target,distFromCenter,absolute coordinates,area)
        self.detectionThreshold=TEMPLATE_MATCH_THRESHOLD
        self.run_counter=1
        self.override=False
        self.pause=False
        self.imageParams=None
        self.cmdQueue=cmdQueue
        self.dataQueue=dataQueue
        self.lock=threading.Lock()
        #call super class init method and bind to instance
        threading.Thread.__init__(self)
        print "Tracking no targets!"
    def getDefaultMainColorProfile(self,targetStr):
        return self.default[targetStr][0]
    def getMainColorProfile(self,targetStr):
        return self.targetColorProfiles[targetStr][0]
    def setMainColorProfile(self,targetStr,newProfile):
        #the main color profile is the first color profile listed in the color profiles list for each target
        self.targetColorProfiles[targetStr][0]=newProfile
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
    def getWallCoordinates(self):
        ans=self.wallCoordinates[:]
        self.dataQueue.put(ans)
        return ans
    def getTargetDistFromCenter(self,target="all"):
        data=None
        if target in self.targetLocations:
            data = self.targetLocations[target]
        else:
            if target=="all":
                data = self.bestTargetOverall
        if data!=None:
            (target,(xdist,ydist),(xClosest,yClosest),areat,(xCOM,yCOM))=data
            self.dataQueue.put((xdist,ydist))
            return (xdist,ydist)
        else:
            self.dataQueue.put(None)
            return None
                
    def isClose(self,target="all"):
        if target in self.targetLocations:
            sample=self.targetLocations[target]
        else:
            if target=="all":
                sample=self.bestTargetOverall
        if sample==None:
            self.dataQueue.put(False)
            return False
        else:
            targetStr,(xDiff,yDiff),(xAbs,yAbs),area,(xCOM,yCOM)=sample
            imageData=self.imageParams
            if imageData==None:
                self.dataQueue.put(False)
                return False
            (x1,y1),center,leftExt,rightExt=imageData
            if area>=CLOSE_THRESHOLD or yAbs>=(y1*float(3/4)):
                self.dataQueue.put(True)
                return True
            else:
                self.dataQueue.put(False)
                return False
    def captureImage(self):
        image=cv.QueryFrame(self.capture)
        downSampledImage=cv.CreateImage((480,240),8,3)
        cv.Resize(image,downSampledImage)
        self.imageParams=self.findCenterOfImageAndExtremes(downSampledImage)
        return downSampledImage
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
    def detectCircle(self,processedImage,contours,area):
        circ=np.array([[]])
        print "got to hough"
        hough_in=cv.CreateImage(cv.GetSize(processedImage),8,1)
        cv.Copy(processedImage,hough_in)
        cv.Smooth(hough_in, hough_in, cv.CV_GAUSSIAN, 15, 15, 0, 0)
        cv.ShowImage("t",hough_in)
        image2=np.asarray(cv.CloneImage(hough_in)[:,:])
        circ=cv2.HoughCircles(image2, cv.CV_HOUGH_GRADIENT, 3, 300, None, 100, 40)
        print "making circles"
        if circ==None:
            return False
        for circle in circ[0]:
            (x,y,radius)=circle
            cv2.circle(image2,(x,y), radius,cv.CV_RGB(255, 0, 0), 2, 8, 0)
            cv2.imshow("t",image2)
        print "return true"
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
    def renderImages(self,original,edgeLinePoints,processedImages,allTargetLocations):
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
        for (edgeStartP,edgeEndP) in edgeLinePoints:
            cv.Line(overlay, edgeStartP, edgeEndP, (0,0,255), 3)
        if self.bestTargetOverall!=None:
            (target,(xdist,ydist),(x,y),areat,(xCOM,yCOM))=self.bestTargetOverall
            cv.Circle(overlay, (x,y), 2, (0, 0, 255), 20)
        cv.Add(original, overlay, original)
        #cv.Merge(completeProcessedImage, None, None, None, original)
        cv.ShowImage('Ball Tracker Processed',original)
    def explore(self,image):
        initialProcessedImage=self.processImage(image)
        (processedImages,targetLocations)=self.findTargets(initialProcessedImage)
        points=self.findWalls(initialProcessedImage)
        self.renderImages(image,points,processedImages,targetLocations)
    def findTargets(self,initialProcessedImage):
        #remove top of image
        ignoreTargetRegions=self.wallTargets
        ignoreRegions=[]
        for ignoreTargetRegion in ignoreTargetRegions:
            (data,processedImagePhase2)=self.findTarget(initialProcessedImage,ignoreTargetRegion)
            if data!=None:
                ((xdist,ydist),(x,y),areat,(xCOM,yCOM),centers)=data
                ignoreRegion=y
                ignoreRegions.append(ignoreRegion)
        targetLocations=[]
        processedImages=[]
        maxTargetArea=0
        maxTargetY=0
        maxTargetLocation=None
        if len(self.targets)!=0:
            for target in self.targets:
                (targetsData,processedImagePhase2)=self.findTarget(initialProcessedImage,target,ignoreRegions)
                processedImages.append(processedImagePhase2)
                if targetsData==None:
                    continue
                (xdist,ydist),(x,y),areat,(xCOM,yCOM),centers=targetsData
                if areat>maxTargetArea and y>maxTargetY:
                    maxTargetArea=areat
                    maxTargetY=y
                    maxTargetLocation=(target,(xdist,ydist),(x,y),areat,(xCOM,yCOM))
                targetLocations.extend(centers)
            self.bestTargetOverall=maxTargetLocation
        else:
            (targetsData,processedImagePhase2)= self.findTarget(initialProcessedImage,None)
            processedImages.append(processedImagePhase2)
        return (processedImages,targetLocations)
    def findTarget(self,processedImage,target,ignoreRegions=None):
         #3 in away=3386655.0 pixel area
        image=cv.CloneImage(processedImage)
        #process image
        if target==None or target not in self.targetColorProfiles:
            colorProfiles=[((256,256,256),(256,256,256))]
        else:
            colorProfiles=self.targetColorProfiles[target]
        processedImagePhase2=self.processImagePhase2(processedImage,colorProfiles[0])
        for i in range(1,len(colorProfiles)):
            currentProcessedImagePhase2=self.processImagePhase2(processedImage,colorProfiles[i])
            cv.Add(processedImagePhase2,currentProcessedImagePhase2,processedImagePhase2)
        moments,area=self.findMomentsAndArea(processedImagePhase2)
        (xCOM,yCOM)=self.findCenterOfMass(moments,area)
        data=(None,processedImagePhase2)
        savedData=None
        if self.updateCheck((xCOM,yCOM),area):
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
                        if ignoreRegions!=None and len(ignoreRegions)!=0 and target in self.ballTargets:
                            #if the target is a ball we want to remove any ball colors seen above boundaries
                            ignoreRegion=max(ignoreRegions) #get greatest y, lowest region in image where bounding object is at
                            if y1>ignoreRegion:#if the target is below the bounding region then it is acceptable
                                centers.append((area1,(x1,y1)))
                        else:
                            centers.append((area1,(x1,y1)))
                contours=contours.h_next()
            if len(centers)!=0:
                closest=max(centers)
                areat,(xClosest,yClosest)=closest
                #print areat
                xdist=xClosest-image.width/float(2)
                ydist=image.height/float(2)-yClosest
                data=(((xdist,ydist),(xClosest,yClosest),areat,(xCOM,yCOM),centers),processedImagePhase2)
                savedData=(target,(xdist,ydist),(xClosest,yClosest),areat,(xCOM,yCOM))
        self.targetLocations[target]=savedData
        return data
    ##################################################################################################
    #Wall Detection
    ##################################################################################################
    def findWalls(self,processedImage,filt="main"):
        c1,c2,ap,rh,deg,th,min_l,max_d,bwt=self.edgeDetectionProfiles["main"]
        image2=None
        for wallTarget in self.wallTargets:
            colorProfile=self.targetColorProfiles[wallTarget][0]
            newProcessed=self.processImagePhase2(processedImage,colorProfile)
            if image2==None:
                image2=newProcessed
            else:
                cv.Add(image2,newProcessed,image2)
        image2=np.asarray(cv.CloneImage(image2)[:,:])
        #(thresh,bw) = cv2.threshold(image2, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        edges = cv2.Canny(image2, c1, c2,apertureSize=ap)
        lines = cv2.HoughLinesP(edges, rh, math.pi/180*deg, th, None, min_l, max_d)
        points=[]
        points1=[]
        if lines==None:
            lines=[[]]
        for line in lines[0]:
            pt1 = (line[0],line[1])
            pt2 = (line[2],line[3])
            points.append((pt1,pt2))
            points1.append((line[0],line[1],line[2],line[3]))
        image2=cv.fromarray(image2)
        self.wallCoordinates=points1
        return points
    def detectQR(self,processedImage):
        pass
    def parseCMD(self,cmd):
        method,args=cmd
        func=getattr(self,method)
        func(*args)
    def stop(self):
        self.active=False
        print "Stopping Vision System"
    def run(self):
        print "Starting Vision System"
        if self.capture==None:
            self.stop()
            return "Camera Init Failed!"
        while self.active:
            if not self.pause:
                try:#try to execute target find
                    #print self.targets[self.target]
                    #print self.getTargetDistFromCenter()
                    if not self.cmdQueue.empty():
                        self.parseCMD(self.cmdQueue.get())
                    image=self.captureImage()
                    #self.findTargets(image)
                    #self.findWalls(image,filt="main")
                    self.explore(image)
                    #print "found targets"
                    cv.WaitKey(1)
                except:
                    #if an exception occurs, to prevent the program from terminating
                    #we just skip this loop and try again
                    print "Error occurred, but program is continuing!"
                    continue
        print "Stopping Vision System"
        #destroy capture 
        del(self.capture)
        cv.DestroyWindow("Tracker")
if __name__=="__main__":
    run=VisionSystemWrapper()
