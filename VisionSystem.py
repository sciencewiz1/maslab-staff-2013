import cv
import numpy
import serial
import scipy
import time
import threading
TEMPLATE_MATCH_THRESHOLD=5562633.0
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
        self.targets={"redBall":cv.LoadImage("redBallTemplate.jpg"),"greenBall":cv.LoadImage("greenBallTemplate.jpg"),"pyramidTopTemplate":cv.LoadImage("pyramidTopTemplate.jpg")}
        self.targetLocationsFromCenter={"redBall":None,"greenBall":None,"pyramidTopTemplate":None}
        #call super class init method and bind to instance
        threading.Thread.__init__(self)

    def processImage(self):
        pass
    '''
    This method locates a desired target in an image.
    @param image- an cv image file, ascertained by doing cv.LoadImage("example.jpg")
    @return a cv image file with a box drawn around the located object and a box drawn
    around the center of the image
    '''
    def findTarget(self,image):
        #reset
        self.targetLocationsFromCenter[self.target]=None
        #rename image variable
        image1=image
        template=self.targets[self.target]
        width = abs(image1.width - template.width)+1
        height = abs(image1.height - template.height)+1
        result_image = cv.CreateImage((width, height), cv.IPL_DEPTH_32F, 1)
        cv.Zero(result_image)
        cv.MatchTemplate(image1, template,result_image,cv.CV_TM_SQDIFF)
        result= cv.MinMaxLoc(result_image)
        (x,y)=result[2]
        minResult=result[0]
        (x2,y2)=(x+template.width,y+template.height)
        center=(int(image1.width/float(2)),int(image1.height/float(2)))
        centerEnd=(int(image1.width/float(2)+template.width),int(image1.height/float(2)+template.height))
        cv.Rectangle(image1,center,centerEnd,(0,0,255),1,0)
        #threshold for ball detection
        #add detector box and update last seen coordinate
        if minResult<=TEMPLATE_MATCH_THRESHOLD:
            cv.Rectangle(image1,(x,y),(x2,y2),(255,0,0),1,0)
            xdist=x-image1.width/float(2)
            ydist=image1.height/float(2)-y
            self.targetLocationsFromCenter[self.target]=(xdist,ydist)
        return image1
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
            cv.ShowImage('Tracker',image1)
            key=cv.WaitKey(2)
            if key==27:
                print "Stopping Vision System"
                self.active=False
                break
        cv.DestroyWindow("Tracker")

if __name__=="__main__":
    test=VisionSystem("redBall")
    test.start() 
#test.changeTarget("greenBall")
#time.sleep(10)
#test.changeTarget("pyramidTopTemplate")
#time.sleep(10)
#test.stop()
