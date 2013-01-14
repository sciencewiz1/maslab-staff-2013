import arduino, time, threading
from constants import *
import sys
sys.path.append("./Vision System")
from VisionSystem import *
import math

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
        '''!!!!!!!'''
        self.roller_motor = arduino.Motor(ard, 5, 51, 11)
        self.roller_motor.setSpeed(ROLLER_SIGN*126)
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
        self.start_time=time.time()
        self.time=self.start_time
        #image processor here
        print "init vision system"
        #self.vs=VisionSystem("redBall")
        '''!!!'''
        self.vs=VisionSystemApp("redBall").getVisionSystem()
        print "starting vs"
        self.vs.start()
        print "started"
        #when turn 360, get IR data (useful for mapping)
        self.ir360={}
        #start timer
        self.wt=WallTimer(self)
        self.wt.start()
#        self.active=True
    #does it see a ball?
    def see(self):
        print "see ball at ",self.vs.getTargetDistFromCenter()
        return self.vs.getTargetDistFromCenter() != None
    def ballCentered(self):
        dist=self.vs.getTargetDistFromCenter()
        if dist== None:
            return 0
        return (math.fabs(dist[0][0])<=CENTER_THRESHOLD)
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
        self.f=open('ir_log.txt','w')
    def run(self):
        while True:
            self.ir_val = self.ir.getValue()
            self.f.write(str(self.ir_val))
            self.f.write('\n')
            #print self.ir_val
            time.sleep(0.1)
            #get one measurement every .1 second
    def obstacleDistance(self):
        return Y_INTERCEPT+SLOPE*self.ir_val

'''PID controller
kp,ki,kd are the constants
desired is the desired value (speed, angle, etc.)
'''
class PIDController:
    def __init__(self,kp, ki, kd):#,input_method,wrapper):
        self.kp=kp
        self.ki=ki
        self.kd=kd
        self.integral=0
        self.last_error=None
        self.last_time=time.time()
        #self.input_method=input_method
        #self.wrapper=wrapper
    def adjust(self,error):
        if self.last_error==None:
            self.last_error=error
        current_time=time.time()
        #error=desired-actual
        #numerically integrate using trapezoidal rule
        self.integral+=.5*(current_time-last_time)*(self.last_error+error)
        print "error= ",error
        print "integral= ",self.integral
        print "derivative= ",self.kd*(error-self.last_error)/(current_time-self.last_time)
        output=self.kp*(error)+self.ki*self.integral+\
                self.kd*(error-self.last_error)/(current_time-self.last_time)
        self.last_time=current_time
        self.last_error=error
        return output

'''Will raise a flag when it's time to abandon balls and go for the wall to score.
(If there are other flags to be raised at certain times, I can abstractify this more.
'''
class WallTimer(threading.Thread):
    def __init__(self,wrapper):
        #IR value
        super(WallTimer, self).__init__()
        self.wrapper=wrapper
    def run(self):
        while time.time()<self.wrapper.start_time+WALL_TIME:
            print "walltimer: ",time.time()-self.wrapper.start_time
            time.sleep(1)
        self.wrapper.mode=WALL_MODE
