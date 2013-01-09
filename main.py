import arduino, time, threading

ard = arduino.Arduino()

#Run arduino
ard.run()

#IR threshold: what counts as "close"?
IR_THRESHOLD = 200.0
#IR threshold: what counts as "too close"?
IR_THRESHOLD2 = 400.0
#when to stop (seconds)
STOP_TIME = 180
#check these signs
LEFT_FORWARD=126
RIGHT_FORWARD=126
LEFT_BACK=-126
RIGHT_BACK=-126


class State:
    def __init__(self,wrap):
        #create a wrapper for arduino that handles all I/O
        self.wrapper=wrap
    def run(self):
        raise NotImplementedError

class ArduinoWrapper:
    def __init__(self, ard):
	print "creating wrapper"
        #Syntax for motors: arduino, currentPic, directionPin, pwmPin
        #Left motor
        self.left_motor = arduino.Motor(ard, 7, 53, 13)
	print "L motor"
        #Right motor
        self.right_motor = arduino.Motor(ard, 6, 52, 12)
	print "R motor"
        #IR sensor
        self.ir_module=IRModule(arduino.AnalogInput(ard, 0))
	print "IR module"
        #start a thread that takes IR readings
        self.ir_module.start()
	print "IR module running"

class StateMachine:
    def __init__(self,wrap):
        #create a wrapper for arduino that handles all I/O
        self.wrapper=wrap
        #self.arduino=ard
    def runSM(self):
        #set the starting state
        self.state=WalkForward(self.wrapper)
	print "set starting state"
        #in the future, categorize states more sophisticatedly (ex. explore)
        while True:
            #does whatever it's supposed to in this state and then transitions
            self.state=self.state.run()
            #repeat indefinitely
            #in the future add a timer, stop when time over threshold

#upgrade this to "explore" later on
class WalkForward(State):
    def run(self):
	print "walk forward"
        #tell left motor to go forward
        self.wrapper.left_motor.setSpeed(LEFT_FORWARD)
        #tell right motor to go forward
        self.wrapper.right_motor.setSpeed(RIGHT_FORWARD)
        #check if there's an obstacle. If so, turn left
        while True:
            #should atomic this
            if self.wrapper.ir_module.ir_val >=IR_THRESHOLD2:
                #way too close, back up
                return Stuck(self.wrapper)
            if self.wrapper.ir_module.ir_val >=IR_THRESHOLD:
                #close, turn left before you get way too close
                return TurnLeft(self.wrapper)
#it might be better to make methods in ArduinoWrapper to do low-level stuff.

class TurnLeft(State):
    def run(self):
	print "turn left"
        #tell only right motor to go forward
        self.wrapper.right_motor.setSpeed(RIGHT_FORWARD)
        self.wrapper.left_motor.setSpeed(0)
        sleep(1)
        return WalkForward(self.wrapper)
    

class TurnRight(State):
    def run(self):
	print "turn right"
        #tell only right motor to go forward
        self.wrapper.right_motor.setSpeed(0)
        #tell only right motor to go forward
        self.wrapper.left_motor.setSpeed(LEFT_FORWARD)
        sleep(1)
        return WalkForward(self.wrapper)
    


#back up until there's enough room
class Stuck(State):
    def run(self):
	print "stuck"
        #tell left motor to go back
        self.wrapper.left_motor.setSpeed(LEFT_BACK)
        #tell right motor to go back
        self.wrapper.right_motor.setSpeed(RIGHT_BACK)
        sleep(1)
        return TurnLeft(State)
    #for now, back up a fixed amount
    

#class Timer:
#    pass
    
class IRModule(threading.Thread):
    def __init__(self,ir2):
        #IR value
	super(IRModule, self).__init__()
	threading.Thread.__init__(self)
        self.ir_val=0
        self.ir=ir2
    def run(self):
        while True:
	    print self.ir_val
            self.ir_val = self.ir.getValue()
	    print self.ir_val
            time.sleep(0.1)
            #get one measurement every second

if __name__ == "__main__":
    wrapper=ArduinoWrapper(ard)
    sm=StateMachine(wrapper)
    sm.runSM()
    
    
