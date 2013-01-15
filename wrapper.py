import arduino, time, threading
from constants import *
import sys
sys.path.append("./Vision System")
from VisionSystem import *
import math
import wx

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
        #Left motor
        self.left_motor = arduino.Motor(self.ard, 7, 53, 13)
        print "L motor"
        #Right motor
        self.right_motor = arduino.Motor(self.ard, 6, 52, 12)
        print "R motor"
        '''!!!!!!!'''
        self.roller_motor = arduino.Motor(self.ard, 5, 51, 11)
        #IR sensor
        self.ir_module=IRModule(arduino.AnalogInput(self.ard, 0))
        print "IR module"
        #start a thread that takes IR readings
        #self.ir_module.start()
        print "IR module running"
        #Run arduino (note this must be done after sensors are set up)
        self.ard.run()
        self.roller_motor.setSpeed(ROLLER_SIGN*126)
        self.mode=BALL_MODE
        self.color=RED#change this when change color!!!
        #last time logged
        self.start_time=time.time()
        self.time=self.start_time
        #image processor here
        print "init vision system"
        #self.vs=VisionSystem("redBall")
        '''!!!'''
        if self.color==RED:
            string="redBall"
        if self.color==GREEN:
            string="greenBall"
        print string
        self.vsApp=VisionSystemApp(string)
        self.vs=self.vsApp.getVisionSystem()
        print "starting vs"
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
class IRModule():#(threading.Thread):
    def __init__(self,ir2):
        #IR value
        #super(IRModule, self).__init__()
        self.ir_val=0
        self.ir=ir2
        self.f=open('ir_log.txt','w')
        self.active=True
    def run(self):
        while self.active:
            self.ir_val = self.ir.getValue()
            self.f.write(str(self.ir_val))
            self.f.write('\n')
            #print self.ir_val
            time.sleep(0)
            #get one measurement every .1 second
        #self.read=False
    #def reset(self):
        #self.read=False
    #def run(self):
        #pass
        #while True:
        #    self.ir_val = self.ir.getValue()
        #    self.read=True
        #    print "IR=",self.ir_val
        #    self.f.write(str(self.ir_val))
        #    self.f.write('\n')
        #    #print self.ir_val
        #    #time.sleep(0.01)
        #    #get one measurement every .1 second
    def getIRVal(self, wait=False):
        #if not wait:
        #    return self.ir_val
        #self.reset()
        #while self.read==False:
        #    pass
        self.ir_val = self.ir.getValue()
        self.f.write(str(self.ir_val))
        self.f.write('\n')
        print "IR=",self.ir_val
        return self.ir_val
    def obstacleDistance(self):
        return Y_INTERCEPT+SLOPE*self.ir_val
    def stop(self):
        self.active=False

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
    def stop(self):
        self.active=False
