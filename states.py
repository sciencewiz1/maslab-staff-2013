import time, threading
from constants import *
from actions import *
from wrapper import *
from random import *
import math
from distance_calculations import *


class Wander(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=GoForward
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
                        
        #see ball, stop wandering
        if self.wrapper.seeBall():
            print "saw ball!"
            return (TurnAndLook,self.wrapper.color)

        #see button, stop wandering
        if self.wrapper.seeButton() and self.wrapper.goForButton():
            print "saw button!"
            return (TurnAndLook,"cyanButton")
        
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
        #I'm not too sure about this.
        #Be careful of robot trying to get an inaccessible ball
        if self.wrapper.seeBall():
            return TurnAndLook
        if stuck_info[0]>=2 or stuck_info[1]>=2:
            return Stuck
        if stuck_info[0]==0 and stuck_info[1]==0:
            return Wander
            #far enough away, stop turning
        #REPLACE THIS WITH COMPASS READING
        elif time.time() > self.wrapper.time+180*TURN_SPEED:
            #return Wander
            return Stuck
            #timeout, stop turning
        else:
            return 0
            #keep turning

class TurnAndLook(State):
    def __init__(self,wrap,target="all",data=()):
        if len(data)==0:
            self.turnTime=0
            self.action=None
        else:
            self.action,self.turnTime=data
        #print "init turn and look"
        State.__init__(self,wrap)
        #if ball is to the right
        #also wall
        #########################################
        #David
        #controlled turn and look variables
        self.turnTime=0
        self.openSpaceTime=None
        self.startTime=time.time()
        #########################################
        dist=wrap.vs.getTargetDistFromCenter(target)
        print "dist ",dist
        if dist==None:
            if DEBUG:
                print "don't see ball"
            if self.action==None:
                if randint(0,1)==0:
                    self.action=TurnLeft
                else:
                    self.action=TurnRight
        #Turn in the direction of the ball (or button) if the ball is in sight
        elif dist[0]>=0:
            if DEBUG:
                print "dist ",dist
                print "see ball to right"
            self.action=TurnRight
        elif dist[0]<0:
            if DEBUG:
                print "dist ",dist
                print "see ball to left"
            self.action=TurnLeft
        #Maybe change to *randomly* (or intelligently choose between)
        #turn left or right
    def stopfunction(self):
        '''
        Priority:
        1. If sensors bumped, back up (Stuck)
        2. If ball is centered, approach (Pause, then ApproachBall)
        3. If see button, and time is appropriate, go for button (Pause, then
        ApproachButton
        4. If turned too long, time out, go wander. (Wander)
        '''
        #########################################
        #David
        #get ir data and record max
        irData=self.wrapper[FRONT_DIST2]
        current=self.openSpaceTime
        if current==None or (irData<current and irData<100): #we found an open space
            self.openSpaceTime=time.time()-self.startTime
        #########################################
        if DEBUG:
            print "Current state: ", self.__class__.__name__
        stuck_info=self.wrapper.stuck()
        if DEBUG:
            print "Stuckness: ",stuck_info
        if stuck_info[0]==3 or stuck_info[1]==3:
            return Stuck
        if self.wrapper.ballCentered():
            if DEBUG:
                print "centered ball, approach!"
            return (Pause, ApproachBall)
            #i.e., first pause and then approach ball
            #return ApproachBall
            #return Stop
            #found ball
        #maybe it should be buttonCentered()?
        if (not self.wrapper.seeBall()) and self.wrapper.seeButton() and\
           self.wrapper.goForButton():
            return (Pause, ApproachButton)
        '''Replace with compass heading'''
        #########################################
        #David
        turnTime1=self.turnTime
        print turnTime1
        if turnTime1!=0 and self.startTime+turnTime1<=time.time():
            #turn time was set and so when we reach this turn time
            #we are heading to open space and so just wander
            print "wandering after turn time"
            return Wander
        #########################################
        if time.time() > self.wrapper.time+360/TURN_SPEED:
            print "now go wander"
            #########################################
            #David 
            #if self.openSpaceTime is not none rotate in the opposite direction
            #for total rotate time-self.openSpaceTime to get to open space
            #self.openSpaceTime is guaranteed to be <=TIMEOUT
            current=self.openSpaceTime
            if current!=None:
                print "found open space"
                action=None
                if isinstance(self.action,TurnRight):
                    action=TurnLeft
                    print "turning left toward open space"
                else:
                    action=TurnRight
                    print "turning right toward open space"
                return (TurnAndLook,(action,current))
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
        if (stuck_info[0]==3 and stuck_info[0]==3) or\
           ((stuck_info[0]==3 or stuck_info[0]==3) and\
            time.time()>=self.wrapper.time+5) or\
           time.time()>=self.wrapper.time+10:
            return Stuck
        #maybe turn in direction *opposite* from that which got it stuck?
            '''!!!'''
            #WARNING: after it gets unstuck it might go towards the same ball again!
            #Need to prevent this!
        if self.wrapper.vs.isClose():
            print "charging b/c ball close"
            return Charge
        if self.wrapper.ballCentered():
            return 0
            #still going after ball
        print "ball not centered!"
        if self.wrapper.seeBall():
            print "still see ball, turn to face."
            return TurnAndLook
            #if you see the ball and it's not centered
        #if lose track of ball
        return Wander
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
            time.time()>=self.wrapper.time+5) or\
           time.time()>=self.wrapper.time+10:
            if stuck_info[0]==3 and stuck_info[1]==3:
                self.wrapper.hitButton()
            return Stuck
        #if within 4 inches
        if self.wrapper[FRONT_DIST]<4:
            return (Charge,"cyanButton")
        if self.wrapper.seeButton():
            return 0
            #still going after button
        print "button not centered!"
        if self.wrapper.seeButton():
            print "still see button, turn to face."
            return TurnAndLook
            #if you see the ball and it's not centered
        #if lose track of ball
        return Wander
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
        if target=="cyanButton":
            self.button=True
    def stopfunction(self):
        if DEBUG:
            print "Current state: ", self.__class__.__name__
        if time.time() > self.wrapper.time+2:
            if self.button==True:
                self.wrapper.hitButton()
                return Stuck
            return TurnAndLook
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
##class Score(State)
##    def __init__(self,wrap):
##        State.__init(self,wrap)
##        self.action=ReleaseBalls
##    def stopfunction(self):
##        if time.time()>self.wrapper.time+3:
##            self.wrapper.mode=BALL_MODE
##            #go collect balls (if time remains)
##            return Stuck
##        return 0

#not yet implemented
class HitPyramidWall(State):
    pass

#not yet implemented
class RealignPyramid(State):
    pass

