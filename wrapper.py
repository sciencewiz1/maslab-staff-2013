import arduino, time, threading
from constants import *
import sys
sys.path.append("./Vision System")
from VisionSystem import *
import math
import wx

FILTER=[.0625,.25, .375, .25, .0625]
F_LEN=len(FILTER)

'''Manual override thread, requires arduino object that it should control!'''
class ManualOverride(threading.Thread):
    def __init__(self,wrapper):
        self.active=True
        threading.Thread.__init__(self)
        self.wrapper=wrapper
    def run(self):
        while self.active:
            print self.active
            cmd=raw_input("Enter command:")
            self.manualOverride(str(cmd))
            time.sleep(0)
    def stop(self):
        self.active=False
    def manualOverride(self,cmd):
        cmds={"l":(LEFT_TURN,-LEFT_TURN,"Left"),"r":(-RIGHT_TURN,RIGHT_TURN,"Right"),"f":(LEFT_FORWARD,RIGHT_FORWARD,"Forward"),"b":(-LEFT_BACK,-RIGHT_BACK,"Backward"),"s":(0,0,"Stop")}
        if cmd in cmds:
            leftSpeed,rightSpeed,cmdName=cmds[cmd]
            time.sleep(0)
            self.wrapper.left_motor.setSpeed(leftSpeed)
            self.wrapper.right_motor.setSpeed(rightSpeed)
            print "Moving "+cmdName
        else:
            print "Invalid command!"
'''Contains all the information and arduino I/O that needs to be passed
between states'''
class Wrapper:
    def __init__(self):
        self.manualControl=False
        self.ard=arduino.Arduino()
        print "creating wrapper"
        #Syntax for motors: arduino, currentPic, directionPin, pwmPin
        self.left_motor = arduino.Motor(self.ard, 3, 51, 9)
        print "Left motor"
        self.right_motor = arduino.Motor(self.ard, 4, 50, 10)
        print "Right motor"
        self.roller_motor = arduino.Motor(self.ard, 2, 53, 8)
        print "Roller motor"
        self.ir_module=IRModule(arduino.AnalogInput(self.ard, 0))
        #start a thread that takes IR readings
        self.ir_module.start()
        '''Add this when we add more IR modules'''
        #self.left_ir_module=IRModule(arduino.AnalogInput(self.ard, 1))
        #self.right_ir_module=IRModule(arduino.AnalogInput(self.ard, 2))
        print "IR module"
        self.left_bump=arduino.DigitalInput(self.ard,1)
        self.right_bump=arduino.DigitalInput(self.ard,2)
        print "Bump sensors"
        self.ard.run()
        self.roller_motor.setSpeed(ROLLER_SIGN*126)
        self.mode=BALL_MODE
        self.color=RED#change this when change color!!!
        #last time logged
        self.start_time=time.time()
        self.time=self.start_time
        #image processor here
        print "init vision system"
        if self.color==RED:
            string="redBall"
        if self.color==GREEN:
            string="greenBall"
        print string
        self.vsApp=VisionSystemApp(string)
        self.vs=self.vsApp.getVisionSystem()
        print "starting vs"
        #start timer
        self.wt=WallTimer(self)
        self.wt.start()
#        self.active=True
    def __getItem__(self,index):
        if index==FRONT_DIST:
            return self.ir_module.distance()
##        if index==LEFT_DIST:
##            return self.left_ir_module.distance()
##        if index==RIGHT_DIST:
##            return self.right_ir_module.distance()
        if index==LEFT_BUMP:
            return self.left_bump.getValue()
        if index==RIGHT_BUMP:
            return self.right_bump.getValue()
        if index==COMPASS:
            return
            #need to return compass value
        if index==X_ACC:
            return
            #to be done
    
    def __setItem__(self,index,value):
        if index==ROLLER_MOTOR:
            self.roller_motor.setSpeed(value)
        elif index==LEFT_MOTOR:
            self.left_motor.setSpeed(value)
        elif index==RIGHT_MOTOR:
            self.right_motor.setSPeed(value)
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
    def turnMotorsOff(self):
        self.left_motor.setSpeed(0)
        self.right_motor.setSpeed(0)
        self.roller_motor.setSpeed(0)
    def resetRoller(self):
        self.roller_motor.setSpeed(ROLLER_SIGN*126)
    def changeCameraNumber(self,index):
        self.vs.changeCameraNumber(index)
    def manualControlCheck(self):
        return self.manualControl
    def connected(self):
        return (self.ard.portOpened, self.ard.port)
    def manualOverride(self):
        self.manualControl=True
        #remove constraints on camera
        self.vs.override=True
        self.manualControl=ManualOverride(self)
        self.manualControl.start()
    def returnToSMMode(self):
        #print "return to sm mode called"
        self.vs.override=False
        self.manualControl.stop()
        #print "trying to stop manual mode"
        #wait for manual control thread to terminate
        self.manualControl.join()
        self.manualControl=False
        #print "sm mode restored"
    def stop(self):
        self.ard.stop()
        self.ir_module.stop()
        self.wt.stop()
        self.vsApp.stop()

'''Module that records IR measurements'''
class IRModule(threading.Thread):
    '''Starts IR thread with an empty list of logged IR values'''
    def __init__(self,ir2,long_range=False):
        #IR value
        #super(IRModule, self).__init__()
        #self.ir_val=0
        self.ir=ir2
        self.f=open('ir_log.txt','w')
        self.active=True
        self.ir_list=[]
        '''set whether this is short or long range'''
        #distance= m*(1/ir)+b
        if long_range:
            self.b=LONG_Y_INTERCEPT
            self.m=LONG_SLOPE
            self.too_far=25
        else:
            self.b=Y_INTERCEPT
            self.m=SLOPE
            self.too_far=12
    '''Continuously get IR values and log them in IR list'''
    def run(self):
        while self.active:
            ir_val=self.ir.getValue()
            print "IR=",ir_val
            self.ir_list.append(ir_val)
            self.f.write(str(ir_val))
            self.f.write('\n')
            #print self.ir_val
            time.sleep(0)
    '''Get IR values. If filtered, gives a weighted average for noise reduction'''
    def getIRVal(self):
        return self.ir_list[-1]
    def __corrected(self,x):
        #given distance, return x+10000 if it's too large
        #then when anything is too large, remember it's an invalid distance
        return (x>self.too_far)*10000+x
    def stop(self):
        self.active=False
    '''distance to obstacle using dist=m*(1/ir)+b'''
    def distance(self, filtered=False):
        #if not filtered, just use last ir value
        if not filtered:
            return self.__corrected(self.m*1/self.getIRVal()+self.b)
        #if filtered but not enough data points yet (because just started)
        #use the first ir value
        if len(self.ir_list)< F_LEN:
            return self.__corrected(self.m*1/self.ir_list[0]+self.b)
        #if filtered, take the last F_LEN ir values and calculate the distances 
        recent_dist=[self.__corrected(self.m*1/ir+self.b) for ir in ir_list[-F_LEN:]])
        #now take a weighted average of the distances
        dist = sum([weight*d for (weight, d) in zip(FILTER,recent_dist)])
        if dist>self.too_far:
            #return an absurdly large number, to indicate out of range
            return 10000
        return dist

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
        self.integral+=.5*(current_time-self.last_time)*(self.last_error+error)
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
        self.active=True
    def run(self):
        while time.time()<self.wrapper.start_time+WALL_TIME and self.active:
            print "walltimer: ",time.time()-self.wrapper.start_time
            time.sleep(1)
        self.wrapper.mode=WALL_MODE
        #Update this once David puts in code to look for walls.
        #self.wrapper.cv.changeTarget("wall")
    def stop(self):
        self.active=False
