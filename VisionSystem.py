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
import sys
from mapper import *
from Tkinter import *
#NOTE: THIS SOFTWARE HAS A MEMORY LEAK! OpenCV Images will start to accumulate in physical memory. After a period of time
#depending on how much RAM your computer has, the system will no longer function and will spawn an error indicating that
#a memory allocation failed! Please plan accordingly!
'''Variable that when set to 1 will provide valuable debug information'''
DEBUG_VISION=0
'''Variable that controls the area threshold for recognizing objects'''
TEMPLATE_MATCH_THRESHOLD=1 #depends on image size
#image dimensions from webcam are: 640x480
#self.targets={"redBall":((0,160,150),(25,255,255))}
#saturation-how much mixed with white
#value-how much mixed with black
#NOTE: This code is still in development stages and commenting has not been completed.
'''This object replaces the standard stdout object so that we can write print statements
to the console and to a file.'''
class StdOut(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
    def flush(self):
        for f in self.files:
            f.flush()
'''This is an interface used to interact with the Vision System Process while
in the main process. All of these methods correspond to methods in the Vision System
Class.'''
class VisionSystemWrapper:
    def __init__(self):
        self.cmdQueue=Queue(1000)
        self.dataQueue=Queue(1000)
        self.VisionSystem=VisionSystemApp(self.cmdQueue,self.dataQueue)
    def addWallTarget(self,targetStr):
        cmd=("addWallTarget",(targetStr,))
        self.cmdQueue.put(cmd)
    def removeWallTarget(self,targetStr):
        cmd=("removeWallTarget",(targetStr,))
        self.cmdQueue.put(cmd)
    def clearWallTargets(self):
        cmd=("clearWallTargets",(targetStr,))
        self.cmdQueue.put(cmd)
    def addTarget(self,targetStr):
        cmd=("addTarget",(targetStr,))
        self.cmdQueue.put(cmd)
    def removeTarget(self,targetStr):
        cmd=("removeTarget",(targetStr,))
        self.cmdQueue.put(cmd)
    def clearTargets(self):
        cmd=("clearTargets",())
        self.cmdQueue.put(cmd)
    def setEdgeDetectionFilter(self,filt):
        cmd=("setEdgeDetectionFilter",(filt,))
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
    def activateEdgeDetection(self):
        cmd=("activateEdgeDetection",())
        self.cmdQueue.put(cmd)
    def deactivateEdgeDetection(self):
        cmd=("deactivateEdgeDetection",())
        self.cmdQueue.put(cmd)
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
class VisionSystemApp(Frame,threading.Thread):
    def __init__(self,cmdQueue,dataQueue):
         #call super class methods
        #Process.__init__(self)
        threading.Thread.__init__(self)
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
        self.vision.stop()
        self.vision.join()
        self.master.quit()
'''Team 12 MASLAB 2013 Vision System API designed to locate certain objects
and command the robot to move towards them'''
class VisionSystem(threading.Thread):
    '''Initialization method that creates the
        camera object and initializes Thread data'''
    #The __init__ method can take a still image and analyze it,
    #if it is given a still, video capture is disabled
    def __init__(self,cmdQueue,dataQueue,still=None):
        #initiate log write
        self.writeLog()
        #create video capture object
        self.capture = cv.CaptureFromCAM(0) #camera object
        #targets list, list of currently tracked targets
        self.targets=[]
        #these lists are used in excluding matched targets
        #if the matched target is a ball target and the ball target
        #is above a found wall target then it is ignored
        #this helps prevent false positives above the field wall
        self.ballTargets=["redBall","greenBall","yellowWall"]
        self.wallTargets=["purpleWall","blueWall"]
        #list used for edge detection (not used in final version of software)
        self.wallCoordinates=[]
        self.frameWriter=None
        if still!=None:
            self.still=cv.LoadImage(still)
        else:
            self.still=None
        #mapper object (not used in final version of software)
        self.mapper=Mapper()
        #used to keep thread alive or kill it, see run() method
        self.active=True
        #boolean that controls if the vision system should do edge detection
        self.detectEdges=False
        #old values
        #"redBall":[((0, 147, 73), (15, 255, 255))
        #color profiles for target detection
        self.targetColorProfiles={"redBall":[((0, 147, 73), (15, 255, 255)),((165, 58, 36), (180, 255, 255))],"greenBall":[((45, 150, 36), (90, 255, 255))],
                      "blueWall":[((103, 141, 94), (115, 255, 255))],"yellowWall":[((27, 108, 18), (34, 255, 255))],
                                  "purpleWall":[((110, 41, 52), (129, 255, 255))],"yellowWall2":[((26, 53,117), (32, 255, 255))],
                                  "cyanButton":[((95,176,115),(108,255,255))]}
        #shape detection, references a function that checks that shape
        self.targetShapeProfiles={"redBall":self.detectCircle,"greenBall":self.detectCircle,
                      "blueWall":self.detectRectangle,"yellowWall":self.detectRectangle,"purpleWall":self.detectRectangle,
                                  "yellowWall2":self.detectRectangle,"cyanButton":self.detectRectangle}
        self.edgeDetectionProfiles={"main":(50,200,3,1,.5,2,70,20,90)} #c1,c2,ap,rh,deg,th,min_l,max_d,bwt
        #two different edge detection types
        #main does color filtering first, thresh just converts to black and white
        self.edgeDetectionFilters=["main","thresh"]
        self.edgeDetectionFilter="main"
        #back up default profiles
        self.default= copy.deepcopy(self.targetColorProfiles)
        self.defaultEdgeDetectionProfiles= copy.deepcopy(self.edgeDetectionProfiles)
        #dictionary that keeps track of where targets are relative to the center
        self.targetLocations={"redBall":None,"greenBall":None,"blueWall":None,"yellowWall":None,"purpleWall":None,
                              "yellowWall2":None,"cyanButton":None}
        #keeps track of the closest target
        self.bestTargetOverall=None #will be (target,distFromCenter,absolute coordinates,area)
        #detection threshold for detected colored objects
        self.detectionThreshold=TEMPLATE_MATCH_THRESHOLD
        self.override=False
        #used to pause vision system
        self.pause=True
        #keeps track of image parameters (size,etc...)
        self.imageParams=None
        #command queue
        self.cmdQueue=cmdQueue
        #data queue
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
        self.pause=False
        print "unpaused"
    def activateEdgeDetection(self):
        self.detectEdges=True
    def deactivateEdgeDetection(self):
        self.detectEdges=False
    def setEdgeDetectionFilter(self,filt):
        if filt in  self.edgeDetectionFilters:
            self.edgeDetectionFilter=filt
        else:
            print "Filter does not exist!"
    '''
    Add a target to be tracked by the VS
    @param targetStr-string that represents target to track, must be present as a key in the self.targetColorProfiles dictionary 
    '''
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
    def addWallTarget(self,targetStr):
        if targetStr in self.targetColorProfiles:
            self.wallTargets.append(targetStr)
        else:
            print "Target: "+str(targetStr)+" is not a valid wall target!"
    def removeWallTarget(self,targetStr):
         if targetStr in self.wallTargets:
            self.targets.remove(targetStr)
         else:
            print "Target: "+str(targetStr)+" is currently not being tracked!"
    def clearWallTargets(self):
        self.targets=[]
    def clearTargets(self):
        self.targets=[]
        print "Targets have been cleared!"
    def getWallCoordinates(self):
        ans=self.wallCoordinates[:]
        self.dataQueue.put(ans)
        return ans
    '''
    Returns (x,y) dist of target center from center of image
    @param target-string representing the target for which you want to know the distance from the center,
    must be "all" or must be present as a key in the self.targetColorProfiles dictionary 
    '''
    def getTargetDistFromCenterOld(self,target="all"):
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
    '''
    Returns (x,y) dist of target center from center of image
    @param target-string or list representing the target(s) for which you want to know the distance from the center,
    must be "all" or must be present as a key in the self.targetColorProfiles dictionary 
    '''
    def getTargetDistFromCenter(self,*targetList):
        if isinstance(targetList[0],list):
            targetList=targetList[0]
        target=self.getClosest(targetList)
        if target==None:
            data=None
            self.dataQueue.put(data)
            return data
        if target=="all":
            target = self.bestTargetOverall[0]
        data=self.targetLocations[target]
        (target,(xdist,ydist),(xClosest,yClosest),areat,(xCOM,yCOM))=data
        self.dataQueue.put((xdist,ydist))
        return data
    '''Of all targets, it gets the closest one'''
    def getClosest(self,targetList):
        closeData=[]
        for target in targetList:
            closeD=self.closeness(target)
            if closeD!=False:
                closeData.append(closeD)
        closest=None
        if len(closeData)!=0:
            closest=max(closeData)
        if closest==None:
            return None
        yAbs,target=closest
        return target
    def closeness(self,target):
        sample=None
        if target in self.targetLocations:
            sample=self.targetLocations[target]
        else:
            if target=="all":
                sample=self.bestTargetOverall
        if sample==None:
            return False
        else:
            targetStr,(xDiff,yDiff),(xAbs,yAbs),area,(xCOM,yCOM)=sample
            return (yAbs,target)
    '''Returns true if the closest target of the tracked targets is close'''
    def isClose(self,*targetList):
        if isinstance(targetList[0],list):
            targetList=targetList[0]
        target=self.getClosest(targetList)
        sample=None
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
            #print "ball at:",(xAbs,yAbs)
            #print "image size",(x1,y1)
            if yAbs>=(y1*3/float(4)):
                self.dataQueue.put(True)
                return True
            else:
                self.dataQueue.put(False)
                return False
    def saveVideo(self,image):
        if self.frameWriter==None:
            ((width,height),(center,centerEnd),leftExtreme,rightExtreme)=self.findCenterOfImageAndExtremes(image)
            fps = cv.GetCaptureProperty(self.capture,cv.CV_CAP_PROP_FPS);
            #fourcc = cv.GetCaptureProperty(self.capture,cv.CV_CAP_PROP_FORMAT)
            fourcc=cv.CV_FOURCC('0','0','0','0')
            self.frameWriter = cv2.VideoWriter('out.avi', fourcc, fps, (width, height), True)
        self.frameWriter.write(np.asarray(image[:,:]))
    #uses images
    def captureImage(self,still=None):
        image=still
        if image==None:
            image=cv.QueryFrame(self.capture)
        downSampledImage=cv.CreateImage((480,240),8,3)
        cv.Resize(image,downSampledImage)
        self.imageParams=self.findCenterOfImageAndExtremes(downSampledImage)
        #clean up
        #del(image)
        return downSampledImage
    #uses images
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
        #clean up
        #del(clone)
        #del(blurred)
        return hsv
    #uses images
    def processImagePhase2(self,processedImage,colorProfile):
        lowerBound,upperBound=colorProfile
        #threshold image to get only color we want
        thresholded=cv.CreateImage(cv.GetSize(processedImage),8,1)
        cv.InRangeS(processedImage,lowerBound,upperBound,thresholded)
        #del(processedImage)
        return thresholded
    #uses images
    def detectCircle(self,processedImage,contours,area):
        return True
    #uses images
    def detectRectangle(self,processedImage,contours,area):
        #to be completed
        return True
    #uses images
    def findMomentsAndArea(self,image):
        mat=cv.GetMat(image)
        moments=cv.Moments(mat)
        area=cv.GetCentralMoment(moments,0,0)
        #del(mat)
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
    #uses images
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
    '''Renders all image frames the user sees, added target circles onto captured video to indicate where the vision system
        thinks it has found a target!'''
    def renderImages(self,original,edgeLinePoints,processedImages,allTargetLocations):
        #cv.ShowImage('Ball Tracker Original',original)
        ((width,height),(center,centerEnd),leftExtreme,rightExtreme)=self.findCenterOfImageAndExtremes(original)
        cv.Rectangle(original,center,centerEnd,(0,0,255),1,0)
        overlay = cv.CloneImage(original)
        completeProcessedImage=processedImages[0]
        for i in range(1,len(processedImages)):
            cv.Add(completeProcessedImage,processedImages[i],completeProcessedImage)
            #clean up
            #del(processedImages[i])
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
        #self.mapper.graphToLocalMap(self.getWallCoordinates())
        #mw=MapperWindow(self.mapper.local_map)
        #mw.draw()
        #clean up
        #del(completeProcessedImage)
        #del(overlay)
        #del(original)
    '''Main function that calls each of the individual processing modules.'''
    def explore(self,image):
        if DEBUG_VISION:
            print "in explore"
        initialProcessedImage=self.processImage(image)
        if DEBUG_VISION:
            print "initial processed"
        (processedImages,targetLocations)=self.findTargets(initialProcessedImage)
        if DEBUG_VISION:
            print "found targets"
        points=[]
        if self.detectEdges:
            points=self.findWalls(initialProcessedImage,self.edgeDetectionFilter)
        if DEBUG_VISION:
            print "going to render"
        self.renderImages(image,points,processedImages,targetLocations)
        #del(initialProcessedImage)
        #del(image)
    '''Find Targets Processing Module, takes in an image and will locate the targets speicifed in the target list
    according to the target color profiles and the area thresholds.
    '''
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
            #del(processedImagePhase2)
        targetLocations=[]
        processedImages=[]
        maxTargetArea=0
        maxTargetY=0
        maxTargetLocation=None
        if DEBUG_VISION:
            print "found boundaries"
        if len(self.targets)!=0:
            for target in self.targets:
                (targetsData,processedImagePhase2)=self.findTarget(initialProcessedImage,target,ignoreRegions)
                if DEBUG_VISION:
                    print "found target"
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
            if DEBUG_VISION:
                print "found targets"
        else:
            (targetsData,processedImagePhase2)= self.findTarget(initialProcessedImage,None)
            processedImages.append(processedImagePhase2)
        return (processedImages,targetLocations)
    '''
    Called by findTargets() to find a particular target.
    '''
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
            #clean up
            #del(currentProcessedImagePhase2)
        if DEBUG_VISION:
            print "processed images round 2"
        moments,area=self.findMomentsAndArea(processedImagePhase2)
        (xCOM,yCOM)=self.findCenterOfMass(moments,area)
        if DEBUG_VISION:
            print "got moments"
        data=(None,processedImagePhase2)
        savedData=None
        if self.updateCheck((xCOM,yCOM),area):
            if DEBUG_VISION:
                print "updating"
            #create target find overlay
            h=cv.CreateMemStorage(0)
            cloneForContour=cv.CloneImage(processedImagePhase2)
            #find all contours
            contours= cv.FindContours(cloneForContour,h ,cv.CV_RETR_LIST, cv.CV_CHAIN_APPROX_SIMPLE)
            centers=[]
            #iterate through all found contours
            while contours:
                area1=cv.ContourArea (contours)
                #if the contour area is above a threshold it is probably a valid target
                if area1>=TEMPLATE_MATCH_THRESHOLD:
                    if DEBUG_VISION:
                        print "found object above thresh"
                    #see if found contour matches shape description
                    objectMatch=self.targetShapeProfiles[target](processedImagePhase2,contours,area1)
                    if DEBUG_VISION:
                        print "object matching"
                    if objectMatch:
                        moments1 = cv.Moments(contours)
                        if DEBUG_VISION:
                            print "found object match"
                        #print list(contours)
                        x1 = int(cv.GetSpatialMoment(moments1, 1, 0)/area1) 
                        y1 = int(cv.GetSpatialMoment(moments1, 0, 1)/area1)
                        #cv.DrawContours(image,contours,(0,255,0),(0,255,0),1,20,1)
                        #ignore the object detected if a blue wall is detected and the the object is above the wall
                        #helps prevent detecting objects from audience
                        #ignore region is essentially the region above the horizontal line that represents the y coordinate
                        #of the center of mass of the blue wall detected
                        if DEBUG_VISION:
                            print "ignore regions",ignoreRegions
                        if ignoreRegions!=None and len(ignoreRegions)!=0 and target in self.ballTargets:
                            if DEBUG_VISION:
                                print "ignoring"
                            #if the target is a ball we want to remove any ball colors seen above boundaries
                            ignoreRegion=max(ignoreRegions) #get greatest y, lowest region in image where bounding object is at
                            if y1>ignoreRegion:#if the target is below the bounding region then it is acceptable
                                if DEBUG_VISION:
                                    print "found ignorable"
                                centers.append((area1,(x1,y1)))
                        else:
                            centers.append((area1,(x1,y1)))
                if DEBUG_VISION:
                    print "next cont"
                contours=contours.h_next()
            if DEBUG_VISION:
                print "explored contours"
            if len(centers)!=0:
                closest=max(centers)
                areat,(xClosest,yClosest)=closest
                if DEBUG_VISION:
                    print "closest"+str(yClosest)
                #print areat
                xdist=xClosest-image.width/float(2)
                ydist=image.height/float(2)-yClosest
                data=(((xdist,ydist),(xClosest,yClosest),areat,(xCOM,yCOM),centers),processedImagePhase2)
                savedData=(target,(xdist,ydist),(xClosest,yClosest),areat,(xCOM,yCOM))
        if DEBUG_VISION:
            print "save data"
        self.targetLocations[target]=savedData
        #clean up
        #del(cloneForContour)
        #del(image)
        return data
    ##################################################################################################
    #Wall Detection
    ##################################################################################################
    #uses images
    #main filter-uses color profiling
    #thresh filter-just uses thresholding
    def findWalls(self,processedImage,filt="main"):
        blurred=cv.CreateImage(cv.GetSize(processedImage),8,3)
        cv.Smooth(processedImage,blurred,cv.CV_GAUSSIAN, 11,11)
        c1,c2,ap,rh,deg,th,min_l,max_d,bwt=self.edgeDetectionProfiles["main"]
        if filt=="main":
            image2=None
            for wallTarget in self.wallTargets:
                colorProfile=self.targetColorProfiles[wallTarget][0]
                newProcessed=self.processImagePhase2(processedImage,colorProfile)
                if image2==None:
                    image2=newProcessed
                else:
                    cv.Add(image2,newProcessed,image2)
                #del(newProcessed)
            image2=np.asarray(cv.CloneImage(image2)[:,:])
        if filt=="thresh":
            blurred=np.asarray(cv.CloneImage(blurred)[:,:])
            gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
            (thresh,bw) = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            image2=bw
        cv2.imshow("Edge Detection Computer Vision",image2)
        cv2.imwrite("edge.jpg",image2)
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
        #clean up
        #del(blurred)
        #del(edges)
        #del(lines)
        #del(image2)
        return points
    '''Detect QR codes. This part of the VS was abandoned!'''
    def detectQR(self,processedImage):
        pass
    def writeLog(self):
        self.log=open("vision_log.txt",'w')
        sys.stdout = StdOut(sys.stdout,self.log)
        self.err_log = open('error.log', 'w')
    '''Parses a string command from the cmd queue
        and executes the corresponding command.
    '''
    def parseCMD(self,cmd):
        method,args=cmd
        func=getattr(self,method)
        func(*args)
    '''Terminates the vision system'''
    def stop(self):
        self.active=False
        self.log.close()
        self.err_log.close()
        del(self.frameWriter);
        print "Stopping Vision System"
    '''This is was is continuously run to operate the vision system. Please investigate
    Python Threading for more information.'''
    def run(self):
        print "Starting Vision System"
        if self.capture==None:
            self.stop()
            return "Camera Init Failed!"
        while self.active or self.override:
            #get command
            if not self.cmdQueue.empty():
                self.parseCMD(self.cmdQueue.get())
            if not self.pause or self.override:
                #I surround all the code by a try,catch combo so that if there is an error on
                #a particular run of the VS code, the entire process will not terminate.
                try:#try to execute target find
                    #print self.targets[self.target]
                    #print self.getTargetDistFromCenter()
                    if self.still==None:
                        image=self.captureImage()
                    else:
                        image=self.captureImage(self.still)
                    if DEBUG_VISION:
                        print "Loaded Image"
                    #process image, detect targets, edge detection
                    #self.saveVideo(image)
                    self.explore(image)
                    if DEBUG_VISION:
                        print "processed"
                    if self.still!=None:
                        cv.WaitKey(0)
                    cv.WaitKey(1)
                    #del(image)
                except Exception, err:
                    print err
                    #if an exception occurs, to prevent the program from terminating
                    #we just skip this loop and try again
                    print "Error occurred, but program is continuing!"
                    self.err_log.write(str(err))
                #continue
        print "Stopping Vision System"
        #destroy capture 
        del(self.capture)
        cv.DestroyWindow("Tracker")
#a few vision system tests
def testVS():
    cmdQueue=Queue(1000)
    dataQueue=Queue(1000)
    run=VisionSystem(cmdQueue,dataQueue,"ex4.jpg")
    run.addTarget("greenBall")
    run.activate()
    run.start()
    #for i in range(1,100):
    #    print run.getTargetDistFromCenter("redBall")
    #    print run.isClose("redBall")
    #    print run.getTargetDistFromCenter(["redBall","greenBall"])
    #    print run.isClose(["redBall","greenBall"])
    #    print run.getTargetDistFromCenter("all")
    #    print run.isClose("all")
def testVS1():
    run=VisionSystemWrapper()
    run.activate()
if __name__=="__main__":
    testVS1()

        
