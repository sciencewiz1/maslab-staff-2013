import time, threading
from constants import *
from actions import *
from wrapper import *
from random import *
import math
from distance_calculations import *
from mapper import *
import pyglet
def playSound(number):
    relativePath="./audio/"
    soundList=["Beeping and whistling.mp3","Excited R2D2.mp3","Proud R2D2.mp3"]
    fileName=soundList[number]
    sound = pyglet.media.load(relativePath+fileName, streaming=False)
    sound.play()
class Wander(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=GoForward
        playSound(0)
    def stopfunction(self):
        '''
        In order of priority:
        1. If bumped against wall, back up.
        2. If see ball, turn to ball.
        3. If too close to wall, back up.
        4. If close to wall, swerve to avoid.
        '''

        if DEBUG:
            print "Current state: ", self.__class__.__name__
        
        #if either bump sensor is pressed, we are stuck!

        #0 is fine, 3 is very stuck
        stuck_info=self.wrapper.stuck()
        if DEBUG:
            print "Stuckness: ",stuck_info

        #0 is left, 1 is right
        if stuck_info[0]>=2 or stuck_info[1]>=2:
            return Stuck
                        
        #see target, stop wandering
        target_seen=self.wrapper.seeTarget()
        if target_seen:
            print "saw ",target_seen
            return (TurnAndLook,target_seen)
        
        #close, turn left before you get way too close
        if stuck_info[0]>=1 or stuck_info[0]>=1:
            return AvoidWall

        #timeout
        if time.time()>self.wrapper.time+5:
            return TurnAndLook
        
        #keep wandering
        return 0


class AvoidWall(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        stuck_info=self.wrapper.stuck()
        #if more stuck on the LHS
        if stuck_info[0]> stuck_info[1]:
            self.action=TurnRight
        #if more stuck on the RHS
        elif stuck_info[0]< stuck_info[1]:
            self.action=TurnLeft
        #if equally stuck on both sides
        else:
            if randint(0,1)==0:
                self.action=TurnLeft
            else:
                self.action=TurnRight
    def stopfunction(self):
        '''
        In order of priority:
        1. If bumped against wall, back up. (Stuck)
        2. If see ball, turn to ball. (TurnAndLook))
        3. If too close to wall, back up. (Stuck)
        4. If no longer close to wall, stop turning and move forwards. (Wander)
        5. If turned 180 degrees and still close to wall, assume it's stuck. (Stuck)
        '''
        if DEBUG:
            print "Current state: ", self.__class__.__name__
        
        #0 is fine, 3 is very stuck
        stuck_info=self.wrapper.stuck()
        if DEBUG:
            print "Stuckness: ",stuck_info
        
        if stuck_info[0]==3 or stuck_info[1]==3:
            return Stuck
        #Be careful of robot trying to get an inaccessible ball
        #see ball, stop wandering
        target_seen=self.wrapper.seeTarget()
        if target_seen:
            print "saw ",target_seen
            return (TurnAndLook,target_seen)
        
        if stuck_info[0]>=2 or stuck_info[1]>=2:
            return Stuck
        if stuck_info[0]==0 and stuck_info[1]==0:
            return Wander
            #far enough away, stop turning
        #REPLACE THIS WITH COMPASS READING
        if time.time() > self.wrapper.time+180/TURN_SPEED:
            #return Wander
            return Stuck
            #timeout, stop turning
        else:
            return 0
            #keep turning

class TurnAndLook(State):
    def __init__(self,wrap,data=()):
        if data==None or data==():
            print "got here"
            self.target="all"
            otherData=()
        elif data.__class__==str:
            self.target=data
            otherData=()
        else:
            self.target,otherData=data
            print "g12"
        if self.target==None:
            self.target="all"
            print "d12"
        if len(otherData)==0:
            self.desiredIR=0
            self.action=None
            self.goToOpen=True
            print "got here 1234"
        else:
            self.action,self.desiredIR,self.goToOpen=otherData
            print "lol1234"
        print self.desiredIR,self.action,self.goToOpen,self.target
        #print "init turn and look"
        State.__init__(self,wrap)
        #if ball is to the right
        #also wall
        #########################################
        #David
        #controlled turn and look variables
        self.openSpaceIR=None
        #########################################
        dist=wrap.vs.getTargetDistFromCenter(self.target)
        print "dist ",dist
        if dist==None:
            if DEBUG:
                print "don't see target"
            if self.action==None or not self.goToOpen:
                if randint(0,1)==0:
                    self.action=TurnLeft
                else:
                    self.action=TurnRight
        #Turn in the direction of the ball (or button) if the ball is in sight
        elif dist[0]>=0:
            if DEBUG:
                print "dist ",dist
                print "see target to right"
            self.action=TurnRight
        elif dist[0]<0:
            if DEBUG:
                print "dist ",dist
                print "see target to left"
            self.action=TurnLeft
        print "started turn and look with target, ",self.target
    def stopfunction(self):
        print "got to stop"
        '''
        Priority:
        1. If sensors bumped, back up (Stuck)
        2. If ball is centered, approach (Pause, then ApproachBall)
        3. If see button, and time is appropriate, go for button (Pause, then
        ApproachButton)
        4. If turned too long, time out, go wander. (Wander)
        '''
        if DEBUG:
            print "Current state: ", self.__class__.__name__
        stuck_info=self.wrapper.stuck()
        #########################################
        #David
        #get ir data and record max
        irData=self.wrapper[FRONT_DIST2]
        current=self.openSpaceIR
        if (current==None or irData>current) and irData>=20 and self.goToOpen and stuck_info==(0,0): #we found an open space
            self.openSpaceIR=irData
        #########################################

        if DEBUG:
            print "Stuckness: ",stuck_info
        if stuck_info[0]==3 or stuck_info[1]==3:
            return Stuck
        target_seen=self.wrapper.seeTarget()
        print "target seen: ",target_seen
        target_cent=self.wrapper.targetCentered(target_seen)
        if target_cent:
            if target_seen==self.wrapper.color:
                print "centered ball, approach!"
                return (Pause, ApproachBall)
            #i.e., first pause and then approach ball
            #return ApproachBall
            #return Stop
            #found ball
        #maybe it should be buttonCentered()?
            if target_seen=="cyanButton":
                print "centered button, approach!"
                return (Pause, ApproachButton)
            if target_seen=="yellowWall":
                print "centered wall, approach!"
                return ApproachWall
            if target_seen=="purplePyramid":
                print "centered pyramid, approach!"
                return ApproachPyramid
        '''Replace with compass heading'''
        #########################################
        #David
        desiredIR=self.desiredIR
        irData1=self.wrapper[FRONT_DIST2]
        if desiredIR!=0 and irData1>=desiredIR-2 and stuck_info==(0,0):
            #turn time was set and so when we reach this turn time
            #we are heading to open space and so just wander
            print "we re-found the open space"
            return Wander
        #########################################
        if time.time() > self.wrapper.time+360/TURN_SPEED:
            print "now go wander"
            #########################################
            #David 
            #if self.openSpaceTime is not none rotate in the opposite direction
            #for total rotate time-self.openSpaceTime to get to open space
            #self.openSpaceTime is guaranteed to be <=TIMEOUT
            if self.goToOpen:
                return Wander
##                current=self.openSpaceIR
##                if current!=None:
##                    print "found open space"
##                    action=None
##                    if isinstance(self.action,TurnRight):
##                        action=TurnLeft
##                        print "turning left toward open space"
##                    else:
##                        action=TurnRight
##                        print "turning right toward open space"
##                    return (TurnAndLook,(self.target,(action,current,False)))
##                else:
##                    return Wander
            else:
            #########################################
                return Wander
            #return TurnAndLook
            #turned 360, no balls in sight
            #log the IR readings during turning.
            #in the future, should probably change direction
            #NEED TO DETECT WHICH PLACES ARE MORE OPEN!
        else:
            print "keep turning"
            return 0
            #keep turning
        
class ApproachBall(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=(ForwardToTarget, wrap.color)
    def stopfunction(self):
        '''
        Priority:
        1. If sensors bumped, or takes too long, give up (Stuck)
        2. If close to ball, prepare to capture (Charge)
        3. If ball no longer centered, turn to face the ball. (TurnAndLook)
        4. If lose track of ball, wander. (Wander)
        '''
        if DEBUG:
            print "Current state: ", self.__class__.__name__
        stuck_info=self.wrapper.stuck()
        if DEBUG:
            print "Stuckness: ",stuck_info
        #note presence of AND here: give up when both sensors bumped,
        #or when one sensor bumped and time too long, or too long
        if (stuck_info[0]==3 and stuck_info[1]==3) or\
           ((stuck_info[0]==3 or stuck_info[1]==3) and\
            time.time()>=self.wrapper.time+3) or\
           time.time()>=self.wrapper.time+6:
            return Stuck
        #maybe turn in direction *opposite* from that which got it stuck?
            '''!!!'''
            #WARNING: after it gets unstuck it might go towards the same ball again!
            #Need to prevent this!
        if self.wrapper.vs.isClose():
            print "charging b/c ball close"
            return (Charge, self.wrapper.color)
        if self.wrapper.ballCentered():
            return 0
            #still going after ball
        print "ball not centered!"
        if self.wrapper.seeBall():
            print "still see ball, turn to face."
            return TurnAndLook
            #if you see the ball and it's not centered
        #if lose track of ball
        return TurnAndLook
#Note: need to do something about inaccessible balls?

#note this is very similar to ApproachBall
class ApproachButton(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=(ForwardToTarget, "cyanButton")
    def stopfunction(self):
        '''
        Priority:
        1. If sensors bumped, or takes too long, give up (Stuck)
        2. If close to button, prepare to charge (Charge)
        3. If button no longer centered, turn to face the button. (TurnAndLook)
        4. If lose track of button, wander. (Wander)
        '''
        if DEBUG:
            print "Current state: ", self.__class__.__name__
        
        stuck_info=self.wrapper.stuck()
        if DEBUG:
            print "Stuckness: ",stuck_info
        #note presence of AND here: give up when both sensors bumped,
        #or when one sensor bumped and time too long, or too long
        if (stuck_info[0]==3 and stuck_info[1]==3) or\
           ((stuck_info[0]==3 or stuck_info[1]==3) and\
            time.time()>=self.wrapper.time+3) or\
           time.time()>=self.wrapper.time+6:
            if stuck_info[0]==3 and stuck_info[1]==3:
                self.wrapper.hitButton()
            return Stuck
        #if within 4 inches
        if self.wrapper[FRONT_DIST]<4 or self.wrapper[FRONT_DIST2]<4:
            print "charging cyan button"
            return (Charge,"cyanButton")
        if self.wrapper.targetCentered("cyanButton"):
            return 0
            #still going after button
        print "button not centered!"
        if self.wrapper.seeButton():
            print "still see button, turn to face."
            return TurnAndLook
            #if you see the button and it's not centered
        #if lose track of button
        return TurnAndLook
#Note: need to do something about inaccessible balls
#optimally, it wouldn't go for balls over walls.


#back up for 1 second
#(this is not very sophisticated right now)
class Stuck(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=GoBack
    def stopfunction(self):
        if DEBUG:
            print "Current state: ", self.__class__.__name__
        if time.time() > self.wrapper.time+BACK_UP_TIME:
            return TurnAndLook
        return 0
        #keep turning
    
class Charge(State):
    def __init__(self,wrap,target=None):
        State.__init__(self,wrap)
        self.action=GoForward
        self.button=False
        self.target=target
        playSound(1)
    def stopfunction(self):
        if DEBUG:
            print "Current state: ", self.__class__.__name__
        stuck_info=self.wrapper.stuck()
        if self.target=="cyanButton":
            if time.time>self.wrapper.time+2 or (stuck_info[0]==3 and stuck_info[1]==3):
                return Stuck
        if self.target in ["redBall","greenBall"]:
            if time.time()>self.wrapper.time+2:
                self.wrapper.balls_collected+=1
                return TurnAndLook
            if (stuck_info[0]==3 and stuck_info[1]==3):
                self.wrapper.balls_collected+=1
                return Stuck
        if self.target in ["yellowWall","purplePyramid"]:
            if time.time()>self.wrapper.time+5 or (stuck_info[0]==3 and stuck_info[1]==3):
                return Score
        return 0
        #keep capturing

class Pause(State):
    def __init__(self, wrap,next_state=ApproachBall):
        State.__init__(self,wrap)
        self.action=DoNothing
        self.next_state=next_state
    def stopfunction(self):
        if DEBUG:
            print "Current state: ", self.__class__.__name__
        if time.time()>self.wrapper.time+0.5:
            print "transition to...", self.next_state.__name__
            return self.next_state
        return 0

class MaxRandom(State):
    def __init__(self,wrap,next_state=TurnAndLook):
        State.__init__(self,wrap)
        a=randint(0,2)
        if a==0:
            self.action=MaxTurnLeft
        elif a==1:
            self.action=MaxTurnRight
        elif a==2:
            self.action=GoBack
        self.next_state=next_state
    def stopfunction(self):
        if DEBUG:
            print "Current state: ", self.__class__.__name__
        if time.time()> self.wrapper.time+2:
            return self.next_state
        return 0

#Uncomment this once we get the bump sensors, wall recognition, and ball release working
#and we're ready for scoring

##class AlignWithWall(State)
##    def __init__(self,wrap):
##        State.__init__(self,wrap)
##        self.action=GoForward
##    def stopfunction(self):
##        if (wrapper.left_bump.getValue()==1 and wrapper.right_bump.getValue()==1)\
##           or time.time()-self.wrapper.start_time>=STOP_TIME-1:
##            return Score
##        #if aligning with wall takes too long
##        #back up and try again
##        if time.time()>self.wrapper.time+5:
##            return Stuck
##        return 0
##
class Score(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=ReleaseBalls
        playSound(2)
    def stopfunction(self):
        if time.time()>self.wrapper.time+5:
            self.wrapper[RELEASE_MOTOR]=CLOSED
            self.wrapper.mode=BALL_MODE
            a=165
            if time.time()>=wrapper.start_time+150:
                a=180
            self.wrapper.wt=WallTimer(a)
            self.wrapper.wt.start()
            self.wrapper.vs.clearTargets()
            self.wrapper.vs.addTarget("redBall")
            self.wrapper.vs.addTarget("greenBall")
            #might as well gulp up everything after it's emptied
            #balls and there's <1 minute left.
            #go collect balls (if time remains)
            return Stuck
        return 0

#not yet implemented
#class HitPyramidWall(State):
#    pass

class ApproachWall(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=(ForwardToTarget, "yellowWall")
    def stopfunction(self):
        if DEBUG:
            print "Current state: ", self.__class__.__name__
        
        stuck_info=self.wrapper.stuck()
        if DEBUG:
            print "Stuckness: ",stuck_info
        #note presence of AND here: give up when both sensors bumped,
        #or when one sensor bumped and time too long, or too long
        if (stuck_info[0]==3 and stuck_info[1]==3) or\
           ((stuck_info[0]==3 or stuck_info[1]==3) and\
            time.time()>=self.wrapper.time+3) or\
           time.time()>=self.wrapper.time+6:
            #if stuck_info[0]==3 and stuck_info[1]==3:
            #    self.wrapper.hitButton()
            return Stuck
        #if within 4 inches
        if self.wrapper.targetClose("yellowWall"):#self.wrapper[FRONT_DIST]<4 or self.wrapper[FRONT_DIST2]<4:
            return (Charge,"yellowWall")
        if self.wrapper.targetCentered("yellowWall")!=None:
            return 0
            #still going after button
        print "button not centered!"
        if self.wrapper.seeWall():
            print "still see wall, turn to face."
            return TurnAndLook
            #if you see the ball and it's not centered
        #if lose track of ball
        return TurnAndLook

class ApproachPyramid(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=(ForwardToTarget, "yellowWall2")
        wrap.vs.activateEdgeDetection()
        self.mpr=Mapper()
    def stopfunction(self):
        lines=self.wrapper.vs.getWallCoordinates()
        self.mpr.graphToLocalMap(lines)
        if DEBUG:
            print "Current state: ", self.__class__.__name__
        stuck_info=self.wrapper.stuck()
        if DEBUG:
            print "Stuckness: ",stuck_info
        #note presence of AND here: give up when both sensors bumped,
        #or when one sensor bumped and time too long, or too long
        if (stuck_info[0]==3 and stuck_info[1]==3) or\
           ((stuck_info[0]==3 or stuck_info[1]==3) and\
            time.time()>=self.wrapper.time+3) or\
           time.time()>=self.wrapper.time+6:
            #if stuck_info[0]==3 and stuck_info[1]==3:
            #    self.wrapper.hitButton()
            wrap.vs.deactivateEdgeDetection()
            return Stuck
        #query mapper:
        if self.mpr.pyramidCorner():
            return RealignPyramid
        #if within 4 inches
        if self.wrapper.targetClose("purplePyramid"):#self.wrapper[FRONT_DIST]<4 or self.wrapper[FRONT_DIST2]<4:
            wrap.vs.deactivateEdgeDetection()            
            return (Charge,"purplePyramid")
        if self.wrapper.targetCentered("purplePyramid")!=None:
            return 0
            #still going after button
        print "button not centered!"
        if self.wrapper.seeWall():
            print "still see wall, turn to face."
            self.wrapper.vs.deactivateEdgeDetection()
            return TurnAndLook
            #if you see the ball and it's not centered
        #if lose track of ball
        self.wrapper.vs.deactivateEdgeDetection()
        return TurnAndLook
        
class RealignPyramid(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=None
    #override run method: this is like planning.
    def run(self):
        if DEBUG:
            print "Running ",self.__class__.__name__
            #print "Init action ",self.action.__name__
        self.wrapper[LEFT_MOTOR]=0
        self.wrapper[RIGHT_MOTOR]=0
        time.sleep(0.1)
        self.mpr=Mapper()
        lines=self.wrapper.vs.getWallCoordinates()
        self.mpr.graphToLocalMap(lines)
        corner=self.mpr.pyramidCorner()
        if corner==None:
            return ApproachPyramid
        #calculate how much to turn
        x=corner[0][0]
        y=corner[0][1]
        a=corner[1]
        print "x,y,a: ",x,y,a
        t1=(atan2(y,x)-a)/TURN_SPEED
        t2=((6.5+math.hypot(x,y))*math.sin(math.atan2(y,-x)+a*math.PI/180)+\
           .5*PYRAMID_SIDE)/SPEED
        print "t1,t2: ",t1,t2
        start_time=time.time()
        self.wrapper[LEFT_MOTOR]=LEFT_TURN
        self.wrapper[RIGHT_MOTOR]=-RIGHT_TURN
        while time.time()<=start_time+t:
            pass
        start_time=time.time()
        self.wrapper[LEFT_MOTOR]=LEFT_FORWARD
        self.wrapper[RIGHT_MOTOR]=RIGHT_FORWARD
        start_time=time.time()
        while time.time()<=start_time+t2:
            pass
        start_time=time.time()
        self.wrapper[LEFT_MOTOR]=-LEFT_TURN
        self.wrapper[RIGHT_MOTOR]=RIGHT_TURN
        while time.time()<=start_time+90/TURN_SPEED:
            pass
        self.wrapper[LEFT_MOTOR]=-LEFT_TURN
        self.wrapper[RIGHT_MOTOR]=RIGHT_TURN
        return ApproachPyramid
