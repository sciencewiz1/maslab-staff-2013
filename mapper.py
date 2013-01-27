from constants import *
import pygame
import math

#pass in ABSOLUTE when specifying absolute coordinates
ABSOLUTE=0
#pass in RELATIVE when specifying relative position
RELATIVE=1

#find the right constants later
#maybe on-the-go calibration?
#warning: can't be too dependent on initial data
#how far away is the nearest thing it can see?
BOTTOM_DIST=4
Y_INFINITY=0
#camera height
CAM_H=6

#find the closest horizontal line on the ground that the camera can see.
#measure how much of it the camera can see and divide by 2
WIDTH=4

#anything with slope of >2 is considered vertical
SLOPE_THRESHOLD=2
OVERLAP_THRESHOLD=.1

class Feature:
    def __init__(self):
        self.neighbors={}
        self.coordinates=()
    def getError(self):
        raise NotImplementedError
    def getNeighbors(self,avoid=[]):
        newNeighbors=[]
        for i in self.neighbors.values():
            if i not in avoid:
                newNeighbors.append(i)
        return newNeighbors
    def addNeighbor(self,other,side):
        self.neighbors[side]=other
    def coordinates(self):
        return self.coordinates
    def draw(self,window):
        raise NotImplementedError

class Node(Feature):
    def __init__(self,mode,arg=[],arg2=[],arg3=None,floating=False):
        Feature.__init__(self)
        #here arg contains the list of tuples(feature, side) and
        #arglist contains the list of angles
        self.x=None
        self.y=None
        self.floating=floating
        if mode==ABSOLUTE:
            self.x,self.y=arg3
        for ((feature,side),angle) in zip(arg,arg2):
            self[angle]=feature
            feature.addNeighbor(self,side)
    def draw(self, window):
        window.point(self.coordinates())
    def coordinates(self):
        return (self.x,self.y)

class Wall(Feature):
    '''
    arg is length when specifying relative,
    coordinates of endpoints when specifying relative
    '''
    def __init__(self,mode,arg=None,error=0,left=None,right=None,angles=[]):
        #arg is distance in relative mode, and coordinates (x1,x2,y1,y2)
        #in absolute mode
        #if mode==RELATIVE:
        self.length=arg
        #self.floating=floating (Now specified using nodes)
        self.error=error
        self.neighbors={}
        self.neighbors[0]=left
        self.neighbors[1]=right
        self.qr=None
        self.subfeatures={}
        #question: do we store locs of walls separately from locs of nodes?
        #add QR codes!
        #bind to a neighbor!
        if mode==RELATIVE:
            self.distance=arg
        if mode==ABSOLUTE:
            if len(arg)>=2:
                self.pt1=(arg[0],arg[1])
            if len(arg)>=4:
                self.pt2=(arg[3],arg[4])
            self.distance=dist(arg)
            #self.pts=[]
            #for i in xrange(0,(len(arg)+1)/2):
            #    self.pts.append(arg[2*i],arg[2*i+1])           
            self.length=dist(arg)
    def endpoints(self):
        return [self.pt1,self.pt2]
    def coordinates(self):
        return (self.pt1[0],self.pt1[1],self.pt2[0],self.pt2[1])
    def dist(self):
        return self.distance
#    def bind(self):
#        pass
    def draw(self,window):
        window.line(self.coordinates)
        
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


'''given the y-pixel, approximate the y-distance and error'''
def yDist(x,y):
    #approximate the error with the derivative
    error=-1.0*BOTTOM_DIST*Y_PIXELS/((Y_INFINITY-y)*(Y_INFINITY-y))
    return [1.0*BOTTOM_DIST*Y_PIXELS/(Y_INFINITY-y),error]

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

'''helps choose lowermost edges in each edge pic'''
class SegmentList:
    #li consists of (x1,y1,x2,y2)'s in camera pixel space
    def __init__(self,li):
        #the list of line segments
        self.li=li
        #remove segments that are close to vertical, because these are probably vertical edges
        #(they might be bottom/tops of walls, but we ignore this because there's too much
        #error associated to almost-vertical lines.)
        li=self.removeVerts(li)
        xsort={}
        for (i,(x1,y1,x2,y2)) in enumerate(li):
            if x1>x2:
                li[i]=(x2,y2,x1,y1)
            #if x1 not in li.keys():
            #    xsort[x1]=[]
            #if x2 not in li.keys():
            #    xsort[x2]=[]
            xsort[x1]=[]#.append(i)
            xsort[x2]=[]#.append(i)
        for k in xsort:
            for (i,(x1,y1,x2,y2)) in enumerate(li):
                if x1==k:
                    
                #if x1<=k and k<x2:
                #    xsort[k].append(i)
        self.xsort=xsort
        votes=[0 for i in li]
        keylist=xsort.keys()
        keylist.sort()
        for i in xrange(1,len(keylist)):
            #loop through all the segments that have the x-value keylist[i]
            #somewhere in the interior.
            maxj=0
            maxy=-10000
            #remember, y goes downwards in camera coordinates
            for j in xsort[keylist[i]]:
                ym=ymidpt(li[j],keylist[i-1],keylist[i])
                if ym>maxy:
                    maxj=j
                    maxy=ym
            votes[maxj]+=(keylist[i]-keylist[i-1])
        self.votes=votes
        #now see which ones got the most votes
        self.accepted=[]
        for (i,v) in enumerate(votes):
            #if v>=70:
            if v/float(li[2]-li[0])>2.0/3:
                self.accepted.append((li[i],i))
    def removeVerts(self,segment_list):
        horiz=[]
        vert=[]
        for (x1,y1,x2,y2) in segment_list:
            if math.fabs(slope(x1,y1,x2,y2))<2:
                #ignore walls that are <=30 pixels long:they're probably bogus
                horiz.append((x1,y1,x2,y2))
            else:
                vert.append((x1,y1,x2,y2))
            return (horiz,vert)
    def endptList(self,indexed=False):
        elist=[]
        for (i,(x1,y1,x2,y2)) in enumerate(self.li):
            if indexed:
                elist.append((x1,y1,i))
                elist.append((x2,y2,i))
            else:
                elist.append((x1,y1))
                elist.append((x2,y2))
    #find all segments with endpoints close to a given point
    #t is line, side
    def closePoints(self,t,radius=80):
        elist=self.endptList(True)
        closeList=[]
        for (x1,y1,i) in elist:
            if t!= (x1,y1,i) and dist(t[0],t[1],x1,y1)<=radius:
                closeList.append((x1,y1,i))
        return closeList
    def xClosePoints(self,t,radius=20):
        elist=self.endptList(True)
        closeList=[]
        for (x1,y1,i) in elist:
            if t!= (x1,y1,i) and math.fabs(x1-t[0])<=radius:
                closeList.append((x1,y1,i))
        return closeList
    '''find all segments with endpoint close to given point
    and with close intersection'''
    def closeIntersections(self,t,radius=80,allowed_error=20):
        closeList=self.closePoints(t,radius)
        closeIntList=[]
        for (x1,y1,i) in closeList:
            ix,iy=intersection(segment,self.li[i])
            if ix>=min(x1,segment[0])-allowed_error and ix<=max(x1,segment[0])+allowed_error:
                if i not in closeIntList:
                    closeIntList.append((ix,iy,i))
        return closeIntList
    '''for a given line #i and endpoint, do there exist lines approximately
    parallel to that line?
    If so, then there is good evidence the endpoint is a node
    becuase walls are made of 2 parallel lines'''
    def existParallels(self,segment,radius=20):
        closeList=self.xClosePoints(segment,radius)
        for (x,y,i) in closeList:
            if mod180dist(angle(self.li[i]),segment)<10:
                return True
        return False
    def lowlines(self):
        return self.accepted
#    def midpt(self,li):
#        return (float(li[0]+li[1])/2,float(li[2]+li[3])/2)

def ymidpt(li,c1,c2):
        x1,y1,x2,y2=li
        return (y2-y1)/float(x2-x1)*(float(c1+c2)/2-x1)+y1

class MapperWindow:
    def __init__(self):
        self.window=pygame.display.set_mode((1280,960))
        self.offset=(640,480)
    #1 inch = 10 pixels
    def line(self,coord):
        x1,x2,y1,y2=coord
        pygame.draw.line(window,pygame.Color(255,255,255),\
                         self.conv(x1,y1),\
                         self.conv(x2,y2),1)
        pygame.display.flip()
        #update display
    #convert from coordinates in inches to screen coordinates
    def conv(self,x,y):
        PPI=10
        return (self.offset[0]+int(PPI*x),self.offset[1]-int(PPI*y))
    def point(self,coord):
        x,y=coord
        pygame.draw.circle(window, pygame.Color(255,255,255),\
                           self.conv(x,y), 2, 0)
    

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
                pass
                #note: if need to deal with length 3, this would be troublesome.
    

class Mapper:
    #note: need to match walls! here turn data (compass, accelerometer)
    #idea: can convert ir data to map and use hough?
    #be nice
    
    '''given a list of segments, generates a map (returns a Map object)'''
    #segment_list comes from HoughLines
    def graphToLocalMap(self,segment_list):
        low_horiz=[]
#        horiz,vert=self.removeVerts(segment_list)
        iv=SegmentList(segment_list)
        low_horiz=iv.lowlines()
        #these are the low walls.
        #now make them into edges and connect them with nodes.
        nodeList=[]
        #low_horiz looks like ((x1,y1,x2,y2),i)
        for (x1,y1,i) in low_horiz:
            closeIntList=iv.close((x1,y1,i))
            c=centroid(closeIntList)[0:1]
            #ignore
            nodeList.append((closeIntList,c))
        for (x1,y1,i) in low_horiz:
            
        
#            flag=0
#            #-1=delete
#            for (i,p) in enumerate(horiz):
#                for (j,q) in enumerate(horiz):
#                    if i !=j and overlapRatio([p,q])>=OVERLAP_THRESHOLD and\
#                       yCenter(p)>yCenter(q):
#                        flag=1
#                        break
#                if not flag:
#                    low_horiz.append(p)

#    def createLocalMap(self,segment_list):
#        #be careful with edges!
#        #identify close edges?
#        #identify wall behind another wall.
#        if averageIn:
#            return
#            #need to average in previous measurements...
'''
def overlapRatio(li):
    x1=min(li[0][0],li[0][2])
    x2=max(li[0][0],li[0][2])
    x3=min(li[1][0],li[1][2])
    x4=max(li[1][0],li[1][2])
    total=max(x2,x4)-min(x1,x3)
    overlap=min(x2,x4)-max(x1,x3)
    return overlap/total
'''
def yCenter(li):
    return float(li[1]+li[3])/2

def tupleToArg(t):
    if t[1]==None:
        return t[0]
    else:
        return t

def slope(x,y1=None,x2=None,y2=None):
    x1,y1,x2,y2==tupleToArg((x,y1,x2,y2))
    if x1==x2:
        return 1000
    return float(y2-x2)/(y1-x1)

def extrapolate(x3,x,y1=None,x2=None,y2=None):
    x1,y1,x2,y2==tupleToArg((x,y1,x2,y2))
    return slope(x1,y1,x2,y2)*(x3-x1)+y1
    
def dist(x,y1=None,x2=None,y2=None):
    x1,y1,x2,y2==tupleToArg((x,y1,x2,y2))
    return math.hypot(x2-x1,y2-y1)

def angle(x,y1=None,x2=None,y2=None):
    x1,y1,x2,y2==tupleToArg((x,y1,x2,y2))
    return (math.atan2(y2-y1,x2-x1)*180/math.PI)%180

def mod180dist(a,b):
    return min(math.fabs(a-b),180-math.fabs(a-b))

#intersection of 2 line segments defined by their endpoints
def intersection(l1,l2):
    m1=slope(l1)
    m2=slope(l2)
    if m1==m2:
        #if l1[1]-m1*l1[0]!=l2[1]-m2*l2[0]:
        return (10000,10000)
        #parallel lines don't intersect. (10000,10000) represents infinity.
    x3=l2[1]-l1[1]+m1*l1[0]-m2*l2[0]
    y3=m1*(x3-m1[0])+m1[2]
    return (x3,y3)

#li is list of tuples of the same length
def centroid(li):
    l=len(li)
    m=len(li[0])
    out=[]
    for j in xrange(0,m):
        su=0.0
        for t in li:
            su+=t[j]
        out.append(su/l)
    return out

'''
Things to think about: when are two walls close enough to be the same?
'''

#SegmentList test
#iv=SegmentList([(0,0,200,100),(50,100,100,100)])
#print iv.xsort
#print iv.votes
#print iv.accepted
