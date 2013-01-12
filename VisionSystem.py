import cv
import numpy
import serial
import scipy
import time
import threading
TEMPLATE_MATCH_THRESHOLD=25000
#image dimensions from webcam are: 640x480
#NOTE: This code is still in development stages and commenting has not been completed.
'''Team 12 MASLAB 2013 Vision System API designed to locate certain objects
and command the robot to move towards them'''
class VisionSystem(threading.Thread):
    '''Initialization method that creates the
        camera object and initializes Thread data'''
    def __init__(self,target):
        self.capture = cv.CaptureFromCAM(1) #camera object
        self.target=target
        self.active=True
        self.targets={"redBall":((0,180,250),(25,255,255))}
        self.targetLocations={"redBall":None,"greenBall":None,"pyramidTopTemplate":None}
        #call super class init method and bind to instance
        threading.Thread.__init__(self)

    def processImage(self,image):
        #clone image so that we do not tamper with original
        clone=cv.CloneImage(image)
        #blurrs image to reduce color noise
        blurred=cv.Smooth(clone,clone,cv.CV_BLUR, 3)
        #converts image to hsv
        hsv=cv.CreateImage(cv.GetSize(clone),8,3)
        cv.CvtColor(clone,hsv,cv.CV_BGR2HSV)
        #threshold image to get only color we want
        thresholded=cv.CreateImage(cv.GetSize(hsv),8,1)
        lowerBound,upperBound=self.targets[self.target]
        cv.InRangeS(hsv,lowerBound,upperBound,thresholded)
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
    '''
    This method locates a desired target in an image.
    @param image- an cv image file, ascertained by doing cv.LoadImage("example.jpg")
    @return a cv image file with a box drawn around the located object and a box drawn
    around the center of the image
    '''
    def findTarget(self,image):
        image=cv.CloneImage(image)
        #reset
        self.targetLocations[self.target]=None
        #process image
        processedImage=self.processImage(image)
        moments,area=self.findMomentsAndArea(processedImage)
        (x,y)=self.findCenterOfMass(moments,area)
        #find center of image
        length=10
        centerX,centerY=(int(image.width/float(2)),int(image.height/float(2)))
        center=(centerX-length,centerY-length)
        centerEnd=(centerX+length,centerY+length)
        cv.Rectangle(image,center,centerEnd,(0,0,255),1,0)
        cv.ShowImage("t1",processedImage)
        if TEMPLATE_MATCH_THRESHOLD>25000 and (x,y)!=(None,None):
            #create target find overlay
            overlay = cv.CreateImage(cv.GetSize(image), 8, 3)
            cv.Circle(overlay, (x, y), 2, (0, 0, 255), 20) 
            cv.Add(image, overlay, image) 
            #set internal variable of ball location from center point
            xdist=x-image.width/float(2)
            ydist=image.height/float(2)-y
            self.targetLocationsFromCenter[self.target]=((xdist,ydist),area)
            #cv.Merge(processedImage, None, None, None, image)
        return image
    def getTargetDistFromCenter(self):
        return self.targetLocationsFromCenter[self.target]
    def changeTarget(self,target):
        self.target=target
    def stop(self):
        self.active=False
        print "Stopping Vision System"
    def run(self):
        print "Starting Vision System"
        cv.NamedWindow("Tracker", 1 )
        if self.capture=="None":
            self.stop()
            return "Camera Init Failed!"
        while self.active:
            #print self.getTargetDistFromCenter()
            image=cv.QueryFrame(self.capture)
            image1=self.findTarget(image)
            cv.ShowImage('Tracker',image)
            cv.ShowImage('Tracker1',image1)
            key=cv.WaitKey(2)
            if key==27:
                print "Stopping Vision System"
                self.active=False
                break
        cv.DestroyWindow("Tracker")

if __name__=="__main__":
    test=VisionSystem("redBall")
    test.start() 
