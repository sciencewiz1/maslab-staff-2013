import arduino, time, threading
from constants import *
from wrapper import *
from actions import *
from states import *

"""Note: I created specific actions as subclasses of Action, though an
alternative is to make objects of type Action"""

class StateMachine:
    def __init__(self,wrap):
        #create a wrapper for arduino that handles all I/O
        self.wrapper=wrap
        #self.arduino=ard
    def runSM(self):
        #set the starting state
        self.state=Wander(self.wrapper)
        print "set starting state"
        #in the future, categorize states more sophisticatedly (ex. explore)
        while True:
            #does whatever it's supposed to in this state and then transitions
            self.state=self.state.run()
            #repeat indefinitely
            #in the future add a timer, stop when time over threshold

ard = arduino.Arduino()
wrapper=Wrapper(ard)
sm=StateMachine(wrapper)
sm.runSM()
    
    
