from constants import *
import pygame
import math
from huff import *

#pass in ABSOLUTE when specifying absolute coordinates
ABSOLUTE=0
#pass in RELATIVE when specifying relative position
RELATIVE=1

#find the right constants later
#maybe on-the-go calibration?
#warning: can't be too dependent on initial data
#how far away is the nearest thing it can see?
BOTTOM_DIST=4
BOTTOM_WIDTH=4
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
    def __setitem__(self,side,other):
        self.neighbors[side]=other
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
    def __str__(self):
        return "Node at "+str(self.coordinates())
    def draw(self, window):
        print "drawing ",self.coordinates()
        if self.floating:
            window.point(self.coordinates())
        else:
            window.point(self.coordinates(),r=5,w=1)
    def coordinates(self):
        return (self.x,self.y)

class Wall(Feature):
    '''
    arg is length when specifying relative,
    coordinates of endpoints when specifying relative
    '''
    def __init__(self,mode,arg=None,error=0,left=None,right=None):
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
            if arg!=None and len(arg)>=2:
                self.pt1=(arg[0],arg[1])
            if arg!=None and len(arg)>=4:
                self.pt2=(arg[3],arg[4])
            #self.distance=dist(arg)
            #self.pts=[]
            #for i in xrange(0,(len(arg)+1)/2):
            #    self.pts.append(arg[2*i],arg[2*i+1])           
            #self.length=dist(arg)
    def __str__(self):
        return "Segment at "+str(self.coordinates())
    def endpoints(self):
        return [self.pt1,self.pt2]
    def coordinates(self):
        return (self.pt1[0],self.pt1[1],self.pt2[0],self.pt2[1])
    def dist(self):
        return self.distance
#    def bind(self):
#        pass
    def draw(self,window):
        print "drawing ",self.coordinates()
        window.line(self.coordinates())
    def recalc(self):
        self.length=dist(self.neighbors[0].x,self.neighbors[0].y,\
                           self.neighbors[1].x,self.neighbors[1].y)
        self.pt1=(self.neighbors[0].x,self.neighbors[0].y)
        self.pt2=(self.neighbors[1].x,self.neighbors[1].y)
        
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
    error=-1.0*BOTTOM_DIST*2*Y_PIXELS/((Y_INFINITY-y)*(Y_INFINITY-y))
    return [1.0*BOTTOM_DIST*2*Y_PIXELS/(y-Y_INFINITY),error]

def xDist(x,y):
    error=math.sqrt(math.pow(1.0/PIXELS*BOTTOM_WIDTH*Y_PIXELS/(y-Y_INFINITY),2)+\
                    math.pow(float(x-PIXELS)/PIXELS*BOTTOM_WIDTH*Y_PIXELS/(math.pow(Y_INFINITY-y,2)),2))
    return [float(x-PIXELS)/PIXELS*BOTTOM_WIDTH*Y_PIXELS/float(y-Y_INFINITY),error]

    
'''given a (x,y) value, convert it to a distance
for now, assume that 
'''
def pixelToPosition(x,y):
    print "(x,y)=",(x,y)
    xd=xDist(x,y)
    yd=yDist(x,y)
    error=math.sqrt(xd[0]*xd[0]+yd[0]*yd[0])
    print "position=",(xd[0],yd[0])
    return [(xd[0],yd[0]),error]

'''helps choose lowermost edges in each edge pic'''
class SegmentList:
    #li consists of (x1,y1,x2,y2)'s in camera pixel space
    def __init__(self,li):
        #the list of line segments
        self.li=li.tolist()
        #if in reverse order, switch.
        print "self.li:",self.li
        for (i,(x1,y1,x2,y2)) in enumerate(self.li):
            if x1>x2:
                li[i]=(x2,y2,x1,y1)
        #the indices of the elements in li that we actually want to consider
        self.li2=xrange(0,len(li))
        self.xsorted={}
        self.keylist=[]
        self.votes=[]
        self.accepted=[]
        #remove segments that are close to vertical, because these are probably vertical edges
        #(they might be bottom/tops of walls, but we ignore this because there's too much
        #error associated to almost-vertical lines.)
        #self.li2=self.removeVerts(li)
    def removeVerts(self):
        horiz=[]
        vert=[]
        self.li2=[]
        for (i,(x1,y1,x2,y2)) in enumerate(self.li):
            if math.fabs(slope(x1,y1,x2,y2))<2:
                horiz.append((x1,y1,x2,y2))
                self.li2.append(i)
                self.xsorted[x1]=[]
                self.xsorted[x2]=[]
            else:
                vert.append((x1,y1,x2,y2))
        return (horiz,vert)
    '''after calling xsort, self.xsorted will contain a dictionary.
    keys: x-values of segments represented by indices in li2
    values: the index into li and whether it is left/right endpoint or in the
    middle of segment
    keylist is the sorted x-values (sorted keys)'''
    def xsort(self):
        for k in self.xsorted:
            #remember, li2 contains the indices of the accepted segments
            for j in self.li2:
                x1,y1,x2,y2=self.li[j]
                if x1==k and k==x2:
                    self.xsorted[k].append((j,'A'))#segment j is a vertical line
                elif x1==k:
                    self.xsorted[k].append((j,'L'))#k is the left endpt of seg j
                elif x1<k and k<x2:
                    self.xsorted[k].append((j,'M'))#k is in middle of segment j
                elif k==x2:
                    self.xsorted[k].append((j,'R'))#k is the right endpt of j
        self.keylist=self.xsorted.keys()
        self.keylist.sort()
    '''
    stores the indices of the low horizontal segments into self.accepted
    '''
    def low_horiz(self):
        self.votes=[0 for i in self.li]
        for i in xrange(1,len(self.keylist)):
            #loop through all the segments that have the x-value keylist[i]
            #somewhere in the interior.
            maxj=0
            maxy=-10000
            #remember, y goes downwards in camera coordinates
            for (j,char) in self.xsorted[self.keylist[i]]:
                #(j,char) are the indices of segments that contain the ith x-value
                #and char says whether the x-value is in the left, middle, or right
                if char!='L' and char!='A':
                #(need to make sure it's not leftmost
                    ym=ymidpt(self.li[j],self.keylist[i-1],self.keylist[i])
                    if ym>maxy:
                        maxj=j
                        maxy=ym
            self.votes[maxj]+=(self.keylist[i]-self.keylist[i-1])
        #now see which ones got the most votes
        self.accepted=[]
        for (i,v) in enumerate(self.votes):
            #if v>=70:
            if v/float(self.li[i][2]-self.li[i][0])>2.0/3:
                self.accepted.append(i)
        return self.accepted
    #overloaded.
    #pass in int i to get ith segment
    #pass in tuple (i,j) to get the jth endpoint of ith segment (j=0 or 1)
    #pass in list to get list of segments
    def __getitem__(self,i):
        if i.__class__==list:
            li=[]
            for j in i:
                li.append(self.li[j])
            return li
        if i.__class__==tuple:
            #print i
            return self.endpt(self.li[i[0]],i[1])
        return self.li[i]
    #assume it's a tuple
    def __setitem__(self,i,v):
        print "setting: ",(i,v)
        if i[1]==0:
            print self.li[i[0]]
            self.li[i[0]]=(v[0],v[1],self.li[i[0]][2],self.li[i[0]][3])
            print self.li[i[0]]
        if i[1]==1:
            print self.li[i[0]]
            self.li[i[0]]=(self.li[i[0]][0],self.li[i[0]][1],v[0],v[1])
            print self.li[i[0]]
        print self.li
    def endpt(self,seg,side):
        if side==0:
            return (seg[0],seg[1])
        if side==1:
            return (seg[2],seg[3])
#    def endptList(self,indexed=False):
#        elist=[]
#        for (i,(x1,y1,x2,y2)) in enumerate(self.li):
#            if indexed:
#                elist.append((x1,y1,i))
#                elist.append((x2,y2,i))
#            else:
#                elist.append((x1,y1))
#                elist.append((x2,y2))
    #find all segments with endpoints close to a given point
    #t is (index into li,side)
    #note we exclude t
    def closePoints(self,t,radius=80,double_sided=False):
        close_list=[]
        if double_sided:
            for i in xrange(0,len(self.li)):
                for side in [0,1]:
                    pt1=self[(i,side)]
                    pt2=self[t]
                    print "comparing ",pt1," and ",pt2," in closePoints"
                    print "dist=",dist(pt1[0],pt1[1],pt2[0],pt2[1])
                    if t!=(i,side) and dist(pt1[0],pt1[1],pt2[0],pt2[1])<=radius:
                        print "close!"
                        close_list.append((i,side))
            print "close_list:",close_list
            return close_list
        if not double_sided:
            for i in xrange(0,len(self.li)):
                pt1=self[(i,0)]
                pt2=self[t]
                print "comparing ",pt1," and ",pt2," in closePoints"
                print "dist=",dist(pt1[0],pt1[1],pt2[0],pt2[1])
                if t!=(i,0) and dist(pt1[0],pt1[1],pt2[0],pt2[1])<=radius:
                    close_list.append((i,0))
            return close_list
                
#        elist=self.endptList(True)
#        closeList=[]
#        for (x1,y1,i) in elist:
#            if t!= (x1,y1,i) and dist(t[0],t[1],x1,y1)<=radius:
#                closeList.append((x1,y1,i))
#        return closeList
    def xClosePoints(self,t,radius=20):
        for i in self.li:
            for side in [0,1]:
                pt1=self[(i,side)]
                pt2=self[t]
                if t!=(i,side) and math.fabs(pt1[0]-pt2[0])<=radius:
                    closeList.append((i,side))
        return closeList
        
#        elist=self.endptList(True)
#        closeList=[]
#        for (x1,y1,i) in elist:
#            if t!= (x1,y1,i) and math.fabs(x1-t[0])<=radius:
#                closeList.append((x1,y1,i))
#        return closeList
    '''find all segments with endpoint close to given point
    and with close intersection'''
    def closeIntersections(self,t,radius=90,allowed_error=20,double_sided=True):
    #double_sided=False
        close_list=self.closePoints(t,radius,double_sided)
        print "close points=",close_list
        print "now filter more to get close *intersections*"
        i_list=[]#list of (index, side) of segments that intersect segment t
        int_list=[]#list of intersections
        #tup is (index,side)
        for (i,s) in close_list:
            given=self[t[0]]
            current=self[i]
            print "try to find intersection of lines:",(given, current)
            x0=self[t][0]
            xcur=self[(i,s)][0]
            ix,iy=intersection(given, current)
            print "intersection vs given: ",((ix,iy),given)
            #!!!potential problem: this might recognize a covering
            #wall as splitting up the covered wall
            if ix>=min(x0,xcur)-allowed_error and ix<=max(x0,xcur)+allowed_error:
                #if (i,s) not in closeIntList:
                i_list.append((i,s))
                int_list.append((ix,iy))
        return (i_list,int_list)
    #which side of the segment is the point on?
    #assume seg has x1<x2, and not vertical
    def side(self,seg,pt):
        if pt[0]<=float(seg[0]+seg[2])/2:
            return 0
            #left side
        if pt[0]> float(seg[0]+seg[2])/2:
            return 1
            #right side
        
    '''for a given line #i and endpoint, do there exist lines approximately
    parallel to that line?
    If so, then there is good evidence the endpoint is a node
    becuase walls are made of 2 parallel lines'''
    #EDIT: no, this is not good evidence.
#    def existParallels(self,segment,radius=20):
#        #note segment is (i,s)
#        if self[segment]<=radius or self[segment]>=PIXELS-radius:
#            return False #too close to edge.
#        closeList=self.xClosePoints(segment,radius)
#        for (x,y,i) in closeList:
#            if mod180dist(angle(self.li[i]),segment)<10:
#                return True
#        return False
    def lowlines(self):
        return self.accepted
#    def midpt(self,li):
#        return (float(li[0]+li[1])/2,float(li[2]+li[3])/2)

def ymidpt(li,c1,c2):
        x1,y1,x2,y2=li
        return (y2-y1)/float(x2-x1)*(float(c1+c2)/2-x1)+y1

class MapperWindow:
    def __init__(self,mp):
        self.window=pygame.display.set_mode((1280,960))
        self.offset=(640,480)
        self.m=mp
        self.robot=(0,0)
        self.robot_dir=90
    def drawRobot(self):
        x0=self.robot[0]
        y0=self.robot[1]
        x1=self.robot[0]+2*math.cos(math.pi*(self.robot_dir+150)/180)
        y1=self.robot[1]+2*math.sin(math.pi*(self.robot_dir+150)/180)
        x2=self.robot[0]+2*math.cos(math.pi*(self.robot_dir-150)/180)
        y2=self.robot[1]+2*math.sin(math.pi*(self.robot_dir-150)/180)
        pygame.draw.polygon(self.window,pygame.Color(255,255,255),\
                         [self.conv(x0,y0),self.conv(x1,y1),self.conv(x2,y2)],0)
        pygame.display.flip()
    #1 inch = 10 pixels
    def line(self,coord):
        x1,y1,x2,y2=coord
        pygame.draw.line(self.window,pygame.Color(255,255,255),\
                         self.conv(x1,y1),\
                         self.conv(x2,y2),1)
        pygame.display.flip()
        #update display
    #convert from coordinates in inches to screen coordinates
    def conv(self,x,y=None):
        PPI=10
        if y==None:
            (x,y)=x
        return (self.offset[0]+int(PPI*x),self.offset[1]-int(PPI*y))
    def point(self,coord,r=2,w=0):
        x,y=coord
        pygame.draw.circle(self.window, pygame.Color(255,255,255),\
                           self.conv(x,y), r, w)
    def draw(self):
        for f in self.m.feature_list:
            f.draw(self)
        self.drawRobot()
        #absolute coordinates necessary here. Should not be, though.
    

class Map:
    def __init__(self):
        self.feature_list=[]
    def add(self,obst):
        self.feature_list.append(obst)
    def __str__(self):
        s=""
        for f in self.feature_list:
            s=s+str(f)+"\n"
        return s

class Mapper:
    #note: need to match walls! here turn data (compass, accelerometer)
    #idea: can convert ir data to map and use hough?
    #be nice

    def __init__(self):
        self.local_map=Map()
    
    '''given a list of segments, generates a local map (returns a Map object)
    It is local in the sense that it only uses data from one moment in time.
    '''
    #segment_list comes from HoughLines
    def graphToLocalMap(self,segment_list):
        low_horiz=[]
#        horiz,vert=self.removeVerts(segment_list)
        iv=SegmentList(segment_list)
        iv2=SegmentList(segment_list)
        iv.removeVerts()
        iv.xsort()
        low_horiz=iv.low_horiz()
        #DEBUG
        print "iv list: ",iv.li
        print "low horiz: ", low_horiz
        #low_horiz=iv.lowlines()
        #these are the low walls.
        #now make them into edges and connect them with nodes.
        bound_list=set([])
        #bound_list will contain all bound vertex coordinates
        #hypothesized to be nodes (rather than "floating" nodes)
        node_list=[]
        #low_horiz contains indices of low horizontal segments
        #try to bind the right endpoints first
        for i in low_horiz:
            x1,y1,x2,y2=iv[i]
            close_i_list,close_int_list=iv.closeIntersections((i,1))
            print "low_horiz, i=",i
            #(i,1)=right endpt of segment i
            #first list contains indices pointing to intersecting segments
            #second list contains intersections
            #if there are other segments that intersect our segment
            #near the right endpoint, then it's probably a vertex
            if close_int_list!=[]:
                #average over intersections
                c=centroid(close_int_list)[0:2]
                print "c=",c
                close_i_list.append((i,1))
                node_list.append((close_i_list,c))
                bound_list.add(tuple(c))
            print "low_horiz, i=",i
            print "close lists:\n",close_i_list,"\n",close_int_list
            print "bound_list: ",bound_list
            print "node_list: ",node_list
            #if there aren't other segments that intersect our segment
            #near the right endpoint, but there is a parallel segments that
            #ends near, then it's probably a vertex (because walls are
            #made of 2 parallels
#            elif existParallels((i,1)):
#                node_list.append(([(i,1)],iv[(i,1)]))
#                bound_list.add((i,1))
        #try to find nodes for the left endpoints
#        for i in low_horiz:
#            if (i,0) not in bound_list and existParallels((i,0)):
#                node_list.append(([],iv[(i,1)]))
#                bound_list.add((i,1))
        for (close_i_list,c) in node_list:
            #bind close vertices to c.
            for t in close_i_list:
                iv2[t]=c
        print "iv2=",iv2.li
#        print [iv2[(i,0)] for i in low_horiz]
#        print [iv2[(i,1)] for i in low_horiz]
#        print [iv2[(i,0)] for i in low_horiz]+[iv2[(i,1)] for i in low_horiz]
        node_set=frozenset([iv2[(i,0)] for i in low_horiz]+[iv2[(i,1)] for i in low_horiz])
        node_dict={}
        for pt in node_set:
            actual_pt=pixelToPosition(pt[0],pt[1])[0]#what about error?
            if pt in bound_list:
                n=Node(ABSOLUTE,arg3=actual_pt,floating=False)
            else:
                n=Node(ABSOLUTE,arg3=actual_pt,floating=True)
            node_dict[pt]=n
            self.local_map.add(n)
            print "added node: ",n
        for i in low_horiz:
            lnp=iv2[(i,0)]
            rnp=iv2[(i,1)]
            ln=node_dict[lnp]
            rn=node_dict[rnp]
            w=Wall(ABSOLUTE,arg=None,error=0,left=ln,right=rn)
            self.local_map.add(w)
            #set the wall's neighbors
            w[0]=ln
            w[1]=rn
            angle1=math.atan2(rnp[1]-lnp[1],rnp[0]-lnp[0])*180/math.pi
            angle2=(angle1+180)%360
            #set the nodes' neighbors
            ln[angle1]=w
            rn[angle2]=w
            w.recalc()
                
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

def slope(x1,y1=None,x2=None,y2=None):
    (x1,y1,x2,y2)=tupleToArg((x1,y1,x2,y2))
    if x1==x2:
        return 1000
    return float(y2-y1)/(x2-x1)

def extrapolate(x3,x,y1=None,x2=None,y2=None):
    x1,y1,x2,y2=tupleToArg((x1,y1,x2,y2))
    return slope(x1,y1,x2,y2)*(x3-x1)+y1
    
def dist(x1,y1=None,x2=None,y2=None):
    x1,y1,x2,y2=tupleToArg((x1,y1,x2,y2))
    return math.hypot(x2-x1,y2-y1)

def angle(x1,y1=None,x2=None,y2=None):
    x1,y1,x2,y2=tupleToArg((x1,y1,x2,y2))
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
    x3=(l2[1]-l1[1]+m1*l1[0]-m2*l2[0])/(m1-m2)
    y3=m1*(x3-l1[0])+l1[1]
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
    print "centroid=:",out
    return out

'''
Things to think about: when are two walls close enough to be the same?
'''

'''this works.
print "hello"
#SegmentList test
iv=SegmentList([(0,0,200,100),(50,100,100,100)])
print iv.removeVerts()
iv.xsort()
iv.low_horiz()
print iv.xsorted
print iv.votes
print iv.accepted
'''

h=Huff("ex4.jpg")
lines=h.huff()[0]
mpr=Mapper()
mpr.graphToLocalMap(lines)
mw=MapperWindow(mpr.local_map)
mw.draw()
print str(mpr.local_map)
