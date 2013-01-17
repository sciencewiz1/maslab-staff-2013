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
        
        #if either bump sensor is pressed, we are stuck!
        if self.wrapper[LEFT_BUMP] or self.wrapper[RIGHT_BUMP]:
            return Stuck

        dist=self.wrapper[FRONT_DIST]
        
        if dist >= TOO_CLOSE:
        #way too close, back up
            return Stuck
        #should change to bump sensor
        
        #see ball, stop wandering
        if self.wrapper.see():
            print "saw ball!"
            return TurnAndLook
        
        #close, turn left before you get way too close
        if dist >= CLOSE:
            return AvoidWall

        #timeout
        if time.time()>self.wrapper.time+5:
            return TurnAndLook
        
        #keep wandering
        return 0


class AvoidWall(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=TurnLeft
        #Maybe change to *randomly* (or intelligently choose between)
        #turn left or right
    def stopfunction(self):
        '''
        In order of priority:
        1. If bumped against wall, back up. (Stuck)
        2. If see ball, turn to ball. (TurnAndLook))
        3. If too close to wall, back up. (Stuck)
        4. If no longer close to wall, stop turning and move forwards. (Wander)
        5. If turned 180 degrees and still close to wall, assume it's stuck. (Stuck)
        '''
        if self.wrapper[LEFT_BUMP] or self.wrapper[RIGHT_BUMP]:
            return Stuck
        dist=self.wrapper[FRONT_DIST]
        #I'm not too sure about this.
        #Be careful of robot trying to get an inaccessible ball
        if self.wrapper.see():
            return TurnAndLook
        if dist>=TOO_CLOSE:
            return Stuck
        if dist <CLOSE:
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
    def __init__(self,wrap):
        #print "init turn and look"
        State.__init__(self,wrap)
        #if ball is to the right
        #also wall
        dist=wrap.vs.getTargetDistFromCenter()
        print "dist ",dist
        if dist==None:
            if DEBUG:
                print "don't see ball"
            if randint(0,1)==0:
                self.action=TurnLeft
            else:
                self.action=TurnRight
        '''Turn in the direction of the ball if the ball is in sight'''
        elif dist[0][0]>=0:
            if DEBUG:
                print "dist ",dist
                print "see ball to right"
            self.action=TurnRight
        elif dist[0][0]<0:
            if DEBUG:
                print "dist ",dist
                print "see ball to left"
            self.action=TurnLeft
        #Maybe change to *randomly* (or intelligently choose between)
        #turn left or right
    def stopfunction(self):
        if DEBUG:
            print "looping in (stopfunction of) ", self.__class__.__name__
        if self.wrapper.ballCentered():
            if DEBUG:
                print "centered ball, approach!"
            return Pause
            #return ApproachBall
            #return Stop
            #found ball
        '''Replace with compass heading'''
        if time.time() > self.wrapper.time+360/TURN_SPEED:
            print "now go wander"
            return Wander
            #return TurnAndLook
            #turned 360, no balls in sight
            #log the IR readings during turning.
            #in the future, should probably change direction
            #for instance, have a TurnTowardsOpen state.
        else:
            print "keep turning"
            return 0
            #keep turning

class ApproachBall(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        #Change to ForwardToBall
        self.action=ForwardToBall
    def stopfunction(self):
        '''
        Priority:
        1. If sensors bumped, or takes too long, give up (Stuck)
        2. If close to ball, prepare to capture (CaptureBall)
        3. If ball no longer centered, turn to face the ball. (TurnAndLook)
        4. If lose track of ball, wander. (Wander)
        '''
        #note presence of AND here: give up when both sensors bumped,
        #or when one sensor bumped and time too long, or too long
        if (self.wrapper[LEFT_BUMP] and self.wrapper[RIGHT_BUMP]) or\
           ((self.wrapper[LEFT_BUMP] or self.wrapper[RIGHT_BUMP]) and\
            time.time()>=self.wrapper.time+5) or\
           time.time()>=self.wrapper.time+10:
            return Stuck
            '''!!!'''
            #WARNING: after it gets unstuck it might go towards the same ball again!
            #Need to prevent this!
        if self.wrapper.vs.isClose():
            return CaptureBall
        if self.wrapper.ballCentered():
            return 0
            #still going after ball
        print "ball not centered!"
        if self.wrapper.see():
            print "still see ball, turn to face."
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
        if time.time() > self.wrapper.time+1:
            return Wander
        return 0
        #keep turning
    
class CaptureBall(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=GoForward
    def stopfunction(self):
        if time.time() > self.wrapper.time+2:
            return TurnAndLook
        return 0
        #keep capturing

class Pause(State):
    def __init__(self, wrap,action=DoNothing):
        State.__init__(self,wrap)
        self.action=action
    def stopfunction(self):
        if time.time()>self.wrapper.time+0.5:
            return self.action
        return 0

class MaxRandom(State):
    def __init__(self,wrap,action=TurnAndLook):
        State.__init__(self,wrap)
        a=randint(0,2)
        if a==0:
            self.action=MaxTurnLeft
        elif a==1:
            self.action=MaxTurnRight
        elif a==2:
            self.action=GoBack
    def stopfunction(self):
        if time.time()> self.wrapper.time+2:
            return self.action
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

