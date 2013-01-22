from constants import *
import pygame
import math

class Feature:
    def getError(self):
        return NotImplementedError
    def getNeighbors(self,avoid=[]):
        newNeighbors=[]
        for i in self.neighbors:
            if i not in avoid:
                newNeighbors.append(i)
        return self.neighbors

class Node(Feature):
    def __init__(self,mode,arg=[],arg2=[]):
        #here arg contains the list of (feature, side) and
        #arglist contains the list of angles
        if mode==RELATIVE:
            pass
            

#pass in ABSOLUTE when specifying absolute coordinates
ABSOLUTE=0
#pass in RELATIVE when specifying relative position
RELATIVE=1
class Wall(Feature):
    '''
    arg is length when specifying relative,
    coordinates of endpoints when specifying relative
    '''
    def __init__(self,mode,arg,floating,error=0,neighbors=[],angles=[]):
        if mode==RELATIVE:
            self.length=arg
            self.floating=floating
            self.error=error
            self.neighbors=neighbors
            self.angles=angles
            self.qr=None
            #add QR codes!
            #bind to a neighbor!
        if mode==ABSOLUTE:
            if len(arg)>=2:
                self.pt1=(arg[0],arg[1])
            if len(arg)>=4:
                self.pt1=(arg[3],arg[4])
            #self.pts=[]
            #for i in xrange(0,(len(arg)+1)/2):
            #    self.pts.append(arg[2*i],arg[2*i+1])           
            self.floating=floating
            self.error=error
            self.length=dist(arg)
    def endpoints(self):
        return [self.pt1,self.pt2]
    def bind(self):
        pass
        
#warning: need to deal with floating endpoints

class PyramidWall(Feature):
    pass


#typical wall lengths: 47.5, 22
#reject a wall that's too short?

class Post(Feature):
    def __init__(self, error, neighbors=[]):
        self.error=error
        self.neighbors=neighbors

class ReferencePoint:
    pass
    #distances and angles to various objects

#find the right constants later
#maybe on-the-go calibration?
#warning: can't be too dependent on initial data
#how far away is the nearest thing it can see?
BOTTOM_DIST=4
Y_INFINITY=0
#camera height
CAM_H=6
'''given the y-pixel, approximate the y-distance and error'''
def yDist(x,y):
    #approximate the error with the derivative
    error=-1.0*BOTTOM_DIST*Y_PIXELS/((Y_INFINITY-y)*(Y_INFINITY-y))
    return [1.0*BOTTOM_DIST*Y_PIXELS/(Y_INFINITY-y),error]

#find the closest horizontal line on the ground that the camera can see.
#measure how much of it the camera can see and divide by 2
WIDTH=4
def xDist(x,y):
    error=math.sqrt(math.pow(1/PIXELS*BOTTOM_WIDTH*Y_PIXELS/(Y_INFINITY-y),2)+\
                    math.pow(x/PIXELS*BOTTOM_WIDTH*Y_PIXELS/(math.pow(Y_INFINITY-y,2)),2))
    return [x/PIXELS*BOTTOM_WIDTH*Y_PIXELS/(Y_INFINITY-y),error]

    
'''given a (x,y) value, convert it to a distance
for now, assume that 
'''
def pixelToPosition(x,y):
    xd=xDist(x,y)
    yd=yDist(x,y)
    error=math.sqrt(xd[1]*xd[1]+yd[1]*yd[1])
    return [(xd[1],yd[1]),error]

class Map:
    def __init__():
        self.feature_list=[]
        self.table={}
    def add(self,obst):
        self.feature_list.append(obst)
        for (i,pt) in enumerate(obst.endpoints()):
            if pt not in self.table.keys():
                self.table[pt]=[]
            self.table[pt].append((obst,i))
            #makes a dictionary, mapping each point to the Feature it's in.
    #identify matching
    def bind(self,dist=1):
        for li in self.table:
            if len(li)>1:
                #note: if need to deal with length 3, this would be troublesome.
    

#anything with slope of >2 is considered vertical
SLOPE_THRESHOLD=2
OVERLAP_THRESHOLD=.1
class Mapper:
    #last_diagram
    def draw(self):
        #show a pygame window with walls

    #note: need to match walls! here turn data (compass, accelerometer)
    #be nice
        
    '''given a list of segments, generates a map'''
    #warning: need broken line detection?!
    def graphToMap(self,segment_list,averageIn=False):
        horiz=[]
        low_horiz=[]
        if not averageIn:
            for (x1,y1,x2,y2) in segment_list:
                if math.fabs(slope(x1,y1,x2,y2))<2 and\
                   math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2))>30:
                    #ignore walls that are <=30 pixels long:they're probably bogus
                    horiz.append((x1,y1,x2,y2))
            flag=0
            #-1=delete
            for (i,p) in enumerate(horiz):
                for (j,q) in enumerate(horiz):
                    if i !=j and overlapRatio([p,q])>=OVERLAP_THRESHOLD and\
                       yCenter(p)>yCenter(q):
                        flag=1
                        break
                if not flag:
                    low_horiz.append(p)

     def createLocalMap(self,segment_list):
         
                                                
#be careful with edges!

#identify close edges?
#identify wall behind another wall.
            
        if averageIn:
            return
            #need to average in previous measurements...

def overlapRatio(li):
    x1=min(li[0][0],li[0][2])
    x2=max(li[0][0],li[0][2])
    x3=min(li[1][0],li[1][2])
    x4=max(li[1][0],li[1][2])
    total=max(x2,x4)-min(x1,x3)
    overlap=min(x2,x4)-max(x1,x3)
    return overlap/total

def yCenter(li):
    return float(li[1]+li[3])/2

def slope(x1,y1,x2,y2):
    if x1==x2:
        return 1000
    return float(y2-x2)/(y1-x1)

def dist(x1,y1,x2,y2):
    return math.hypot(x2-x1,y2-y1)

'''
Things to think about: when are two walls close enough to be the same?
'''
