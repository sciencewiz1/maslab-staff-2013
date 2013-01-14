import arduino, time, threading
from constants import *
from wrapper import *
from actions import *
from states import *

class StateMachine:
    def __init__(self,wrap):
        #create a wrapper for arduino that handles all I/O
        self.wrapper=wrap
        #self.arduino=ard
    def runSM(self):
        #set the starting state
        self.state=TurnAndLook(self.wrapper)
        print "set starting state"
        #in the future, categorize states more sophisticatedly (ex. explore)
        while True:
            #does whatever it's supposed to in this state and then transitions
            self.state=self.state.run()
            print "SM next state"
            #repeat indefinitely
            #in the future add a timer, stop when time over threshold

ard = arduino.Arduino()
wrapper=Wrapper(ard)
#wrapper.left_motor.setSpeed(LEFT_FORWARD)
#wrapper.right_motor.setSpeed(RIGHT_FORWARD)
sm=StateMachine(wrapper)
sm.runSM()
    
    
