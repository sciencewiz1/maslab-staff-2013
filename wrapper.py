import arduino, time, threading
from constants import *
import sys
sys.path.append("./Vision System")
from VisionSystem import *

'''Contains all the information and arduino I/O that needs to be passed
between states'''
class Wrapper:
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
        #Run arduino (note this must be done after sensors are set up)
        ard.run()
        self.mode=BALL_MODE
        self.color=RED
        #last time logged
        self.time=time.time()
        #image processor here
        self.vs=VisionSystem()
        self.vs.start()
    #does it see a ball?
    def see(self):
        print "ball at ",self.vs.getTargetDistFromCenter()
        return self.vs.getTargetDistFromCenter() != None
    def ballCentered(self):
        return (math.fabs(self.vs.getTargetDistFromCenter()[0])<=CENTER_THRESHOLD)
    '''return array of coordinates of balls'''
    def ballCoordinates(self):
        return self.vs.getTargetDistFromCenter()

'''Module that records IR measurements'''
class IRModule(threading.Thread):
    def __init__(self,ir2):
        #IR value
        super(IRModule, self).__init__()
        self.ir_val=0
        self.ir=ir2
    def run(self):
        while True:
            print self.ir_val
            self.ir_val = self.ir.getValue()
            print self.ir_val
            time.sleep(0.1)
            #get one measurement every .1 second
