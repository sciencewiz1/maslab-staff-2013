from constants import *
from wrapper import PIDController
import math
import time

"""An action is a basic movement. It consists of 2 methods:
run: what to do at the beginning of an action (ex. set the motors to go forward)
loop: what to do continuously during the action
An state initializes an action by passing it a method. When method return
false, the action should continue.
Otherwise, the action should terminate.
"""
class Action:
    def __init__(self,wrapper):
        self.wrapper=wrapper
    def start(self, method):
        print "Running ",self.__class__.__name__
        self.run()
        b=method()
        while not b:
            print "time in action: ",time.time()
            if time.time()-self.wrapper.start_time>=STOP_TIME:
                print "stopping"
                return Stop
#            if time.time()-self.wrapper.start_time>=WALL_TIME:
#                self.wrapper.mode=WALL_MODE
            print "calling loop"
            self.loop()
            print "calling stopfunction"
            print "method=",method
            if method==None:
                print "NONONONONONONO!"
            b=method()
        #exit state
        return b
    #run at beginning
    def run(self):
        raise NotImplementedError
    #loop
    def loop(self):
        raise NotImplementedError

"""The following are basic actions."""

class GoForward(Action):
    def run(self):
        self.wrapper.left_motor.setSpeed(LEFT_FORWARD)
        #tell right motor to go forward
        self.wrapper.right_motor.setSpeed(RIGHT_FORWARD)
    def loop(self):
        #in the future put PID controls to keep it going straight
        print "looping ",self.__class__.__name__

class GoBack(Action):
    def run(self):
        self.wrapper.left_motor.setSpeed(LEFT_BACK)
        #tell right motor to go forward
        self.wrapper.right_motor.setSpeed(RIGHT_BACK)
    def loop(self):
        print "looping ",self.__class__.__name__

class TurnLeft(Action):
    def run(self):
        #tell right motor to go forward
        self.wrapper.right_motor.setSpeed(RIGHT_FORWARD)
        #tell left motor to go backwards
        self.wrapper.left_motor.setSpeed(LEFT_BACK)
        #sleep(1)
        #return Wander(self.wrapper)
    def loop(self):
        print "looping ",self.__class__.__name__
#more sophisticated: can update wrapper with angle turned (using sensory input)

class TurnRight(Action):
    def run(self):
        #tell right motor to go backwards
        self.wrapper.right_motor.setSpeed(RIGHT_BACK)
        #tell left right motor to go forward
        self.wrapper.left_motor.setSpeed(LEFT_FORWARD)
        #sleep(1)
        #return Wander(self.wrapper)
    def loop(self):
        print "looping ",self.__class__.__name__

class ForwardToBall(Action):#or GoForward
    def __init__(self,wrapper):
        Action.__init__(self,wrapper)
        self.controller=PIDController(TURN_KP,TURN_KI,TURN_KD)
    def run(self):
        pass
        #self.wrapper.right_motor.setSpeed(0)
        #self.wrapper.left_motor.setSpeed(0)
    def loop(self):
        print "looping ",self.__class__.__name__
        dist=self.wrapper.vs.getTargetDistFromCenter()
        if dist==None:
            return
            #this will exit the ApproachBallState: lost the ball:`(
        adjust=self.controller.adjust(dist[0][0]/8)
        new_left_speed=LEFT_FORWARD+LEFT_SIGN*adjust
        #scale so speeds <=126
        multiplier=max(math.fabs(new_left_speed/126.0),1)
        new_left_speed=int(new_left_speed/multiplier)
        new_right_speed=int(RIGHT_FORWARD/multiplier)
        print "L/R speeds: ",new_left_speed,new_right_speed
        self.wrapper.left_motor.setSpeed(new_left_speed)
        self.wrapper.right_motor.setSpeed(new_right_speed)
        #sleep(0.1)

class DoNothing(Action):
    def run(self):
        self.wrapper.left_motor.setSpeed(0)
        self.wrapper.right_motor.setSpeed(0)
    def loop(self):
        print "looping ",self.__class__.__name__, time.time()

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
    """Return false=0 if keep going, and the next state if transitioning
    (stopfunction is really equivalent to 'next'.)
    """
    def stopfunction(self):
        raise NotImplementedError
    def run(self):
        if DEBUG:
            print "Running ",self.__class__.__name__
            print "Init action ",self.action.__name__
        #check if there's an obstacle. If so, avoid it
        action_instance=self.action(self.wrapper)
        self.wrapper.time=time.time()
        #stopfunction returns the transition
        next_state = action_instance.start(self.stopfunction)
        return next_state(self.wrapper)     

    
class Stop(State):
    def __init__(self,wrap):
        State.__init__(self,wrap)
        self.action=DoNothing
        self.wrapper.vs.stop()
    def stopfunction(self):
        return 0
