import time, threading
from constants import *
from actions import *
from wrapper import *

"""A state of the state machine.
wrapper: States ALWAYS pass the wrapper on to the next state. The wrapper
includes the arduino I/O and any other miscellaneous bits of data.

action: Basic action associated with state

stopfunction: Given the current wrapper state, return the next state if we
should transition, otherwise return false=0
Needs to be implemented in subclasses

The default behavior of the state is just initialize the action and then keep
doing it until stopfunction returns true.
All you need to specify in a subclass is the action and the stopfunction,
unless you want to override the default behavior.
"""
class State:
    def __init__(self,wrap,mode=0):
        #create a wrapper for arduino that handles all I/O
        self.wrapper=wrap
        self.mode=mode
        self.action=None
    def run(self):
        raise NotImplementedError
    """Return false=0 if keep going, and the next state if transitioning
    (stopfunction is really equivalent to 'next'.)
    """
    def stopfunction(self):
        raise NotImplementedError
    def run(self):
        print self.__class__.__name__
        #check if there's an obstacle. If so, avoid it
        action_instance=self.action(self.wrapper)
        self.wrapper.time=time.time()
        #stopfunction returns the transition
        next_state = action_instance.start(self.stopfunction)
        return next_state(self.wrapper)    

class Wander(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=GoForward
    def stopfunction(self):
        if self.wrapper.ir_module.ir_val >=IR_THRESHOLD2:
        #way too close, back up
            return Stuck
        #should change to bump sensor
        
        #see ball, stop wandering
        if self.wrapper.see():
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
        if self.wrapper.ir_module.ir_val <IR_THRESHOLD:
            return Wander
            #far enough away, stop turning
        elif time.time() > self.wrapper.time+270*TURN_SPEED:
            return Wander
            #timeout, stop turning
        else:
            return 0
            #keep turning

class TurnAndLook(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        #if ball is to the right
        if wrap.vs.getTargetDistFromCenter()[0]>=0:
            self.action=TurnRight
        elif wrap.vs.getTargetDistFromCenter()[0]<0:
            self.action=TurnLeft
        elif not wrap.vs.see():
            if random.randint(0,1)==0:
                self.action=TurnLeft
            else:
                self.action=TurnRight
        #Maybe change to *randomly* (or intelligently choose between)
        #turn left or right
    def stopfunction(self):
        if self.wrapper.ballCentered():
            return ApproachBall
            #found ball
        elif time.time() > self.wrapper.time+360*TURN_SPEED:
            return Wander
            #turned 360, no balls in sight
            #in the future, should probably change direction
            #for instance, have a TurnTowardsOpen state.
        else:
            return 0
            #keep turning

class ApproachBall(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=GoForward
    def stopfunction(self):
        if self.wrapper.ballCentered():
            return ApproachBall
            #found ball
        if time.time() > self.wrapper.time+360*TURN_SPEED:
            return Wander
            #turned 360, no balls in sight
        return 0
        #keep turning
        
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
    
#not yet implemented
class CaptureBall(State):
    pass

#not yet implemented
class HitPyramidWall(State):
    pass

#not yet implemented
class RealignPyramid(State):
    pass
    
    
