from constants import *

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
            self.loop()
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
        pass

class GoBack(Action):
    def run(self):
        self.wrapper.left_motor.setSpeed(LEFT_BACK)
        #tell right motor to go forward
        self.wrapper.right_motor.setSpeed(RIGHT_BACK)
    def loop(self):
        pass

class TurnLeft(Action):
    def run(self):
        #tell right motor to go forward
        self.wrapper.right_motor.setSpeed(RIGHT_FORWARD)
        #tell left motor to go backwards
        self.wrapper.left_motor.setSpeed(LEFT_BACK)
        #sleep(1)
        #return Wander(self.wrapper)
    def loop(self):
        pass
#more sophisticated: can update wrapper with angle turned (using sensory input)

class TurnRight(Action):
    def run(self):
        #tell right motor to go backwards
        self.wrapper.right_motor.setSpeed(RIGHT_BACK)
        #tell left right motor to go forward
        self.wrapper.left_motor.setSpeed(LEFT_FORWARD)
        #sleep(1)
        #return Wander(self.wrapper)
