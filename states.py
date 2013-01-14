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
        #
        #return Wander
        #
        if self.wrapper.ir_module.ir_val >=IR_THRESHOLD2:
        #way too close, back up
            return Stuck
        #should change to bump sensor
        
        #see ball, stop wandering
        if self.wrapper.see():
            print "sawball!"
            return TurnAndLook
        
        #close, turn left before you get way too close
        if self.wrapper.ir_module.ir_val >=IR_THRESHOLD:
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
        if self.wrapper.ir_module.ir_val >=IR_THRESHOLD2:
            return Stuck
        #I'm not too sure about this.
        #Be careful of robot trying to get an inaccessible ball
        if self.wrapper.see():
            return TurnAndLook
        if self.wrapper.ir_module.ir_val <IR_THRESHOLD:
            return Wander
            #far enough away, stop turning
        elif time.time() > self.wrapper.time+180*TURN_SPEED:
            return Wander
            #timeout, stop turning
        else:
            return 0
            #keep turning

class TurnAndLook(State):
    def __init__(self,wrap):
        #print "init turn and look"
        State.__init__(self,wrap)
        #if ball is to the right
        dist=wrap.vs.getTargetDistFromCenter()
        print "dist ",dist
        if dist==None:
            if DEBUG:
                print "don't see ball"
            if randint(0,1)==0:
                self.action=TurnLeft
            else:
                self.action=TurnRight        
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
            return ApproachBall #H
            #return Stop#H
            #found ball
        #
        #dist=self.wrapper.vs.getTargetDistFromCenter
        #if dist != None:
        #    if math.fabs(
        #
        #
        if time.time() > self.wrapper.time+360/TURN_SPEED:
            print "now go wander"
            return Wander#H
            #return TurnAndLook#H
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
        if self.wrapper.vs.close():
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

#not yet implemented
class HitPyramidWall(State):
    pass

#not yet implemented
class RealignPyramid(State):
    pass

