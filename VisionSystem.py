import cv
import numpy
import serial
import scipy
import time
import threading
TEMPLATE_MATCH_THRESHOLD=100
CLOSE_THRESHOLD=3386655500.0
VALUE_THRESHOLD=100
SAT_THRESHOLD=100
HUE_THRESHOLD=25
#image dimensions from webcam are: 640x480
#self.targets={"redBall":((0,160,150),(25,255,255))}
#saturation-how much mixed with white
#value-how much mixed with black
#NOTE: This code is still in development stages and commenting has not been completed.
'''Team 12 MASLAB 2013 Vision System API designed to locate certain objects
and command the robot to move towards them'''
class VisionSystem(threading.Thread):
    '''Initialization method that creates the
        camera object and initializes Thread data'''
    def __init__(self,target):
        self.capture = cv.CaptureFromCAM(0) #camera object
        self.target=target
        self.active=True
        self.targets={"redBall":((0,150,150),(25,255,255))}
        self.calibrated=False
        self.targetLocations={"redBall":None,"greenBall":None,"pyramidTopTemplate":None}
        self.detectionThreshold=TEMPLATE_MATCH_THRESHOLD
        #call super class init method and bind to instance
        #self.calibrate()
        threading.Thread.__init__(self)
    def calibrate(self):
        pass
        '''ideas:
        1) modify saturation and value
        2) find the combo that produces an area in the desired range
        3) return that up through the recursion calls in the DP style of making mods
        '''
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
        image=cv.CloneImage(image)
        #reset
        previous=self.getTargetDistFromCenter()
        #self.targetLocations[self.target]=None #H
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
        cv.ShowImage("t1",processedImage)
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
                xdist=x-image.width/float(2)
                ydist=image.height/float(2)-y
                self.targetLocations[self.target]=((xdist,ydist),leftExtreme,rightExtreme,areat)
                cv.Circle(overlay, (x,y), 2, (0, 0, 255), 20)
                #cv.Circle(overlay,leftExtreme,2,(0,0,255),20)
                #cv.Circle(overlay,rightExtreme,2,(0,0,255),20)
                cv.Add(image, overlay, image)
                cv.Merge(processedImage, None, None, None, image)
                #print self.targetLocations[self.target]
            #3 in away=3386655.0 pixel area
            else:
                self.targetLocations[self.target]=None
        return image
    def getTargetDistFromCenter(self):
        return self.targetLocations[self.target]
    def close(self):
        sample=self.targetLocations[self.target]
        if sample==None:
            return False
        else:
            (x,y),left,right,area=sample
            if area>=CLOSE_THRESHOLD:
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
