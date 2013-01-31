import arduino, time, threading
from constants import *
import sys
sys.path.append("./Vision System")
from VisionSystem import *
from multiprocessing import Process, Queue
import math
import wx

FILTER=[.0625, .25, .375, .25, .0625]
F_LEN=len(FILTER)

'''Manual override thread, requires arduino object that it should control!'''
class ManualOverride(wx.Frame):
    title = "Manual Override"
    def __init__(self,wrapper):
        self.active=True
        wx.Frame.__init__(self, wx.GetApp().TopWindow, title=self.title)
        self.wrapper=wrapper
        self.buildGUI()
        self.Show()
    def buildGUI(self):
        self.createWidgets()
    def createWidgets(self):
        self.Bind(wx.EVT_CHAR_HOOK, self.onKey)
        self.Bind(wx.EVT_CLOSE, self.onClose)
    def onKey(self,event):
        key=event.GetKeyCode()
        if key==wx.WXK_DOWN:
            self.onKeyDown(event)
        if key==wx.WXK_UP:
            self.onKeyUp(event)
        if key==wx.WXK_LEFT:
            self.onKeyLeft(event)
        if key==wx.WXK_RIGHT:
            self.onKeyRight(event)
        if key==wx.WXK_SPACE:#stop
            self.manualOverride("s")
        if key==wx.WXK_ALT:#roller on
            self.manualOverride("ro1")
    def onKeyDown(self,event):
        self.manualOverride("b")
    def onKeyUp(self,event):
        self.manualOverride("f")
    def onKeyLeft(self,event):
        self.manualOverride("l")
    def onKeyRight(self,event):
        self.manualOverride("r")
    def onClose(self,event):
        self.stop()
    def stop(self):
        self.wrapper.returnToSMMode()
        self.active=False
        self.Destroy()
    def manualOverride(self,cmd):
        cmds={"l":(-LEFT_TURN,RIGHT_TURN,0,"Left"),"r":(LEFT_TURN,-RIGHT_TURN,0,"Right"),
              "f":(LEFT_FORWARD,RIGHT_FORWARD,0,"Forward"),"b":(LEFT_BACK,RIGHT_BACK,0,"Backward"),
              "s":(0,0,ROLLER_STOP,"Stop"),"lo":(LEFT_FORWARD,0,0,"Left On"),"ro":(0,RIGHT_FORWARD,0,"Right On"),
              "ro1":(0,0,ROLLER_ANGLE,"Roller On Forward"),"rb1":(0,0,-ROLLER_ANGLE,"Roller On Backwards")}
        if cmd in cmds:
            leftSpeed,rightSpeed,rollerSpeed,cmdName=cmds[cmd]
            self.wrapper.left_motor.setSpeed(leftSpeed)
            print "changed left motor to:"+str(leftSpeed)
            self.wrapper.right_motor.setSpeed(rightSpeed)
            print "changed right motor to:"+str(rightSpeed)
            self.wrapper.roller_motor.setAngle(rollerSpeed)
            self.wrapper[RELEASE_MOTOR]=0
            self.wrapper.helix_motor.setSpeed(126)
            print "Moving "+cmdName
        else:
            print "Invalid command!"
'''Contains all the information and arduino I/O that needs to be passed
between states'''
class Wrapper:
    def __init__(self):
        self.manualControl=False
        self.connectedToArduino=False
        self.ard=arduino.Arduino()
        self.startSwitch=arduino.DigitalInput(self.ard,53)
        self.targetSwitch=arduino.DigitalInput(self.ard,51)
        self.smSwitchOverride=False
        print "creating wrapper"
        #Syntax for motors: arduino, currentPin, directionPin, pwmPin
        self.left_motor = arduino.Motor(self.ard, 12, 23, 11)
        #print "Left motor"
        self.right_motor = arduino.Motor(self.ard, 9, 32, 8)
        #print "Right motor"
        self.helix_motor=arduino.Motor(self.ard, 7, 38, 6)
        #print "helix motor"
        #self.roller_motor = arduino.Motor(self.ard, 7, 31, 6)
        self.roller_motor=arduino.Servo(self.ard, 42)
        #print "Roller servo"
        self.release_motor=arduino.Servo(self.ard,43)
        #print "release motor"
        self.ir_module=IRModule(arduino.AnalogInput(self.ard, 0))
        #this one is long-range
        self.ir_module2=IRModule(arduino.AnalogInput(self.ard, 1),offset=.375)
        '''Add this when we add more IR modules'''
        self.left_ir_module=IRModule(arduino.AnalogInput(self.ard, 4))
        self.right_ir_module=IRModule(arduino.AnalogInput(self.ard, 3))
        print "IR module"
        self.left_bump=arduino.DigitalInput(self.ard,50)
        self.right_bump=arduino.DigitalInput(self.ard,52)
        print "Bump sensors"
        #self.imu=IMU(arduino.IMU(self.ard))
        print "imu"
        #self.roller_motor.setValue(1)
        self.mode=BALL_MODE
        self.color=GREEN#change this when change color!!!
        #last time logged
        self.start_time=time.time()
        self.time=self.start_time
        #image processor here
        #start timer
        self.wt=WallTimer(self)
#        self.active=True
    def connect(self):
        if not self.ard.isAlive():
            self.ard.run()
            self.connectedToArduino=True
        else:
            print "Already connected!"
    def startVS(self):
        print "init vision system"
        self.vs=VisionSystemWrapper()
        print "starting vs"
    def start(self):
        if not self.connected:
            print "Not connected to arduino! Please connect and then try again!"
            return False
        self[HELIX_MOTOR]=126
        self[ROLLER_MOTOR]=ROLLER_ANGLE
        self[RELEASE_MOTOR]=0
        on=self[START]
        print on
        while not on and not self.smSwitchOverride:
            on=self[START]
            print "waiting..."
            if self.manualControlCheck():
                print "did not start SM, entering manual override!"
                return False
        target=self[TARGET]
        self.vs.activate()
        print target
        if target==True:
            self.color=RED
        else:
            self.color=GREEN
        print "going for target..."+str(self.color)
        self.vs.addTarget(self.color)
        self.vs.addTarget("cyanButton")
        print "vision system set"
        #start a thread that takes IR readings
        self.ir_module.start()
        self.ir_module2.start()
        self.left_ir_module.start()
        self.right_ir_module.start()
        #self.imu.start()
        self.start_time=time.time()
        self.time=self.start_time
        self.last_button_time=0#last time it pressed the black button
        self.button_presses=0
        self.wt.start()
    def __getitem__(self,index):
        if index==FRONT_DIST:#right front
            return self.ir_module.distance()
        if index==LEFT_DIST:
            return self.left_ir_module.distance()
        if index==RIGHT_DIST:
            return self.right_ir_module.distance()
        if index==FRONT_DIST2:#left front
            return self.ir_module2.distance()
        if index==LEFT_BUMP:
            return self.left_bump.getValue()
        if index==RIGHT_BUMP:
            return self.right_bump.getValue()
        if index==START:
            return self.startSwitch.getValue()
        if index==TARGET:
            return self.targetSwitch.getValue()
        if index==COMPASS:
            return
            #need to return compass value
        if index==X_ACC:
            return
            #to be done
    
    def __setitem__(self,index,value):
        if index==RELEASE_MOTOR:
            self.release_motor.setAngle(value)
        if index==ROLLER_MOTOR:
            self.roller_motor.setAngle(value)
            #self.roller_motor.setValue(1)
        if index==HELIX_MOTOR:
            self.helix_motor.setSpeed(value)
        if index==LEFT_MOTOR:
            self.left_motor.setSpeed(value)
        if index==RIGHT_MOTOR:
            self.right_motor.setSpeed(value)
    #does it see a ball?

    def goForButton(self):
        return self.mode != WALL_MODE and (time.time()>=self.last_button_time) and self.button_presses<4
    
    def hitButton(self):
        self.last_button_time=time.time()
        self.button_presses+=1
    def seeTarget(self):
        if self.seeBall() and self.mode!=WALL_MODE:
            return self.color
            #right now, if in wall mode, then ignore all balls
        if self.goForButton() and self.seeButton():
            return "cyanButton"
        if self.vs.getTargetDistFromCenter("purplePyramid")!=None:
            return "purplePyramid"
        if self.seeWall() and time.time()-start_time>=160:
            return "yellowWall"
        #if sees wall and time is short
        return None
    def seeWall(self):
        print "see wall at ",self.vs.getTargetDistFromCenter(self.color)
        return self.vs.getTargetDistFromCenter("yellowWall") != None
    def seeBall(self):
        print "see ball at ",self.vs.getTargetDistFromCenter(self.color)
        return self.vs.getTargetDistFromCenter(self.color) != None
    def seeButton(self):
        return self.vs.getTargetDistFromCenter("cyanButton") != None
    def ballCentered(self):
        dist=self.vs.getTargetDistFromCenter(self.color)
        if dist== None:
            return 0
        return (math.fabs(dist[0])<=CENTER_THRESHOLD)
    def targetCentered(self,target=None):
        if target==None:
            target=self.seeTarget()
        if target==None:
            return 0
        dist=self.vs.getTargetDistFromCenter(target)
        if dist== None:
            return 0
        return (math.fabs(dist[0])<=CENTER_THRESHOLD)
    '''return array of coordinates of balls'''
    def targetClose(self,target=None):
        if target==None:
            target=self.seeTarget()
        if target==None:
            return None
        return self.vs.isClose(target)
    def ballCoordinates(self):
        return self.vs.getTargetDistFromCenter()

    '''return information about whether the bot is stuck.
    returns (a,b) where a gives the condition of the left side and b the right side.
    0=fine
    1=close to wall
    2=very close to wall
    3=bumped against wall
    '''
    def stuck(self):
        #left side
        l=0
        r=0
        if self[RIGHT_BUMP]:
            r=3
        else:
            r_dist=self[FRONT_DIST]
            if r_dist<=TOO_CLOSE:
                r=2
            elif r_dist<=CLOSE:
                r=1
            #take into account side sensors.
            if self[RIGHT_DIST]<=SIDE_CLOSE:
                r+=1
        if self[LEFT_BUMP]:
            l=3
        else:
            l_dist=self[FRONT_DIST2]
            #left IR can't detect close distances well, so supplement it.
            if l_dist<=TOO_CLOSE or (l_dist<=CLOSE and r>=2) :
                l=2
            elif l_dist<=CLOSE:
                l=1
            if self[LEFT_DIST]<=SIDE_CLOSE:
                l+=1
        return (l,r)
    
    def turnMotorsOff(self):
        self.left_motor.setSpeed(0)
        self.right_motor.setSpeed(0)
        self.roller_motor.setAngle(ROLLER_STOP)
        #self.roller_override.setValue(0)
    def resetRoller(self):
        self.roller_motor.setAngle(ROLLER_ANGLE)
        #self.roller_motor.setValue(1)
    def changeCameraNumber(self,index):
        self.vs.changeCameraNumber(index)
    def connected(self):
        return (self.ard.portOpened, self.ard.port)
    def manualControlCheck(self):
        return self.manualControl
    def manualOverride(self):
        self.manualControl=True
        #remove constraints on camera
        self.manualControl=ManualOverride(self)
    def returnToSMMode(self):
        self.manualControl=False
    def stop(self):
        self[LEFT_MOTOR]=0
        self[RIGHT_MOTOR]=0
        self[HELIX_MOTOR]=0
        self[ROLLER_MOTOR]=ROLLER_STOP
        #self.ard.stop()
        self.ir_module.stop()
        self.ir_module2.stop()
        self.wt.stop()
        self.vs.stop()
class IMU(threading.Thread):
    def __init__(self,imu):
        self.imu=imu
        self.currentValue=None
        self.active=True
        threading.Thread.__init__(self)
    def getIMUData(self):
        return self.currentValue
    def run(self):
        while self.active:
            self.currentValue=self.imu.getRawValues()
            print self.currentValue
        
'''Module that records IR measurements'''
class IRModule(threading.Thread):
    '''Starts IR thread with an empty list of logged IR values'''
    def __init__(self,ir2,long_range=False,filtering=False,offset=0):
        #IR value
        threading.Thread.__init__(self)
        #self.ir_val=0
        self.f=open('ir_log.txt','w')
        self.active=True
        self.ir_list=[]
        self.offset=0
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
        self.ir=ir2
        self.filtering=filtering
        
    '''Continuously get IR values and log them in IR list'''
    def run(self):
        if not self.filtering:
            while self.active:
                #fix threading issue
                ir_val=self.ir.getValue()
                if self.too_far==25:
                    print "long"
                else:
                    print "short"
                print "IR=",ir_val
                self.ir_list.append(ir_val)
                self.f.write(str(ir_val))
                self.f.write('\n')
                #print self.ir_val
                time.sleep(0.2)
        if self.filtering:
            li=[]
            while self.active:
                for i in xrange(0,3):
                    #fix threading issue
                    ir_val=self.ir.getValue()
                    if self.too_far==25:
                        print "long"
                    else:
                        print "short"
                    print "IR=",ir_val
                    self.li.append(ir_val)
                ir_val=sum(li)/3.0
                self.f.write(str(ir_val))
                self.f.write('\n')
                #print self.ir_val
                time.sleep(0.2)

    '''Get IR values. If filtered, gives a weighted average for noise reduction'''
    def getIRVal(self):
        if len(self.ir_list)==0 or self.ir_list[-1]==None:
            return 50
        else:
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
            ir=self.getIRVal()
            if ir==0:
                ir=1
            ans=self.__corrected(self.m*1/ir+self.b+self.offset)
            return ans
        #if filtered but not enough data points yet (because just started)
        #use the first ir value
        if len(self.ir_list)< F_LEN:
            ans=self.__corrected(self.m*1/self.ir_list[0]+self.b)
            return ans
        #if filtered, take the last F_LEN ir values and calculate the distances 
        recent_dist=[self.__corrected(self.m*1/ir+self.b) for ir in ir_list[-F_LEN:]]
        #now take a weighted average of the distances
        dist = sum([weight*d for (weight, d) in zip(FILTER,recent_dist)])
        if dist>self.too_far:
            #return an absurdly large number, to indicate out of range
            ans=10000
            return ans
        print "dist=",dist
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
    def __init__(self,wrapper,s=WALL_TIME):
        #IR value
        super(WallTimer, self).__init__()
        self.wrapper=wrapper
        self.active=True
        self.s=s
    def run(self):
        while time.time()<self.wrapper.start_time+self.s and self.active:
            print "walltimer: ",time.time()-self.wrapper.start_time
            time.sleep(1)
        self.wrapper.mode=WALL_MODE
        self.wrapper.vs.clearTargets()
        self.wrapper.vs.addTarget("yellowWall")
        #Update this once David puts in code to look for walls.
    def stop(self):
        self.active=False
