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
        self.open=False
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
        if key==wx.WXK_SHIFT: #helix motor
            self.manualOverride("ho")
        if key==wx.WXK_CONTROL: #servo
            if self.open==False:
                self.manualOverride("rlo")
                self.open=True
            else:
                self.manualOverride("rlc")
                self.open=False
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
        cmds={"l":(-LEFT_TURN,RIGHT_TURN,ROLLER_STOP,0,CLOSED,"Left"),
              "r":(LEFT_TURN,-RIGHT_TURN,ROLLER_STOP,0,CLOSED,"Right"),
              "f":(LEFT_FORWARD,RIGHT_FORWARD,ROLLER_STOP,0,CLOSED,"Forward"),
              "b":(LEFT_BACK,RIGHT_BACK,ROLLER_STOP,0,CLOSED,"Backward"),
              "s":(0,0,ROLLER_STOP,0,CLOSED,"Stop"),
              "lo":(LEFT_FORWARD,0,ROLLER_STOP,0,CLOSED,"Left On"),
              "ro":(0,RIGHT_FORWARD,ROLLER_STOP,0,CLOSED,"Right On"),
              "ro1":(0,0,ROLLER_ANGLE,0,CLOSED,"Roller On Forward"),
              "rb1":(0,0,-ROLLER_ANGLE,0,CLOSED,"Roller On Backwards"),
              "ho":(0,0,ROLLER_STOP,HELIX_SPEED,CLOSED,"Helix On Forwards"),
              "hb":(0,0,ROLLER_STOP,-HELIX_SPEED,CLOSED,"Helix On Backwards"),
              "rlo":(0,0,ROLLER_STOP,0,OPEN,"Ball Release Open"),
              "rlc":(0,0,ROLLER_STOP,0,CLOSED,"Ball Release Closed")}
        if cmd in cmds:
            leftSpeed,rightSpeed,rollerSpeed,helixSpeed,releaseMotorSpeed,cmdName=cmds[cmd]
            self.wrapper[LEFT_MOTOR]=leftSpeed
            print "changed left motor to:"+str(leftSpeed)
            self.wrapper[RIGHT_MOTOR]=rightSpeed
            print "changed right motor to:"+str(rightSpeed)
            self.wrapper[ROLLER_MOTOR]=rollerSpeed
            print "changed roller motor to:"+str(rollerSpeed)
            self.wrapper[HELIX_MOTOR]=helixSpeed
            print "changed helix motor to:"+str(helixSpeed)
            self.wrapper[RELEASE_MOTOR]=releaseMotorSpeed
            print "changed release motor to:"+str(releaseMotorSpeed)
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
        #print "creating wrapper"
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
        self.release_motor=arduino.Servo(self.ard,49)
        #print "release motor"
        self.ir_module=IRModule(arduino.AnalogInput(self.ard, 0))
        #this one is long-range
        #self.ir_module2=IRModule(arduino.AnalogInput(self.ard, 1),offset=.375)
        self.ir_module2=IRModule(arduino.AnalogInput(self.ard, 1),True)
        '''Add this when we add more IR modules'''
        self.left_ir_module=IRModule(arduino.AnalogInput(self.ard, 2))
        self.right_ir_module=IRModule(arduino.AnalogInput(self.ard, 7))
        #print "IR module"
        self.left_bump=arduino.DigitalInput(self.ard,50)
        self.right_bump=arduino.DigitalInput(self.ard,52)
        #print "Bump sensors"
        #self.imu=IMU(arduino.IMU(self.ard))
        #print "imu"
        #self.roller_motor.setValue(1)
        self.mode=BALL_MODE
        self.color=GREEN#change this when change color!!!
        #last time logged
        self.start_time=time.time()
        self.time=self.start_time
        #image processor here
        #start timer
        self.wt=WallTimer(self)
        self.balls_collected=0
#        self.active=True
    def connect(self):
        if not self.ard.isAlive():
            self.ard.run()
            self.connectedToArduino=True
        else:
            print "Already connected!"
    def startVS(self):
        #print "init vision system"
        self.vs=VisionSystemWrapper()
        #print "starting vs"
    def start(self):
        if not self.connected:
            print "Not connected to arduino! Please connect and then try again!"
            return False
        self[HELIX_MOTOR]=126
        self[ROLLER_MOTOR]=ROLLER_ANGLE
        self[RELEASE_MOTOR]=CLOSED
        on=self[START]
        while not on and not self.smSwitchOverride:
            on=self[START]
            if self.manualControlCheck():
                print "did not start SM, entering manual override!"
                return False
        target=self[TARGET]
        #print "activating vision"
        self.vs.activate()
        #print "activated vision"
        #print target
        if target==True:
            self.color=RED
        else:
            self.color=GREEN
        print "going for target..."+str(self.color)
        #CHANGED: go for balls of both colors instead.
        self.vs.addTarget(self.color)
        #uncomment this for 2 colors
        #self.vs.addTarget("redBall")
        #self.vs.addTarget("greenBall")
        self.vs.addTarget("cyanButton")
        self.vs.addTarget("blueWall")
        #self.color=["redBall","greenBall"]
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
        #print "called see target"
        if self.seeBall() and self.mode==BALL_MODE:
            return self.color
        print "failed to see ball"
            #right now, if in wall mode, then ignore all balls
        if self.goForButton() and self.seeButton():
            return "cyanButton"
        if self.mode==WALL_MODE and self.seeWall():
            return "yellowWall"
        if self.mode==WALL_MODE and time.time()-self.start_time>=160 and self.vs.getTargetDistFromCenter("purplePyramid")!=None:
            return "purplePyramid"
        #if sees pyramid and time is short
        return None
    def seeWall(self):
        t=self.vs.getTargetDistFromCenter("yellowWall")
        print "see wall at ",t
        return t != None
    def seeBall(self):
        t=self.vs.getTargetDistFromCenter(self.color)
        print "see ball at ",t
        return t != None
    def seeButton(self):
        t=self.vs.getTargetDistFromCenter("cyanButton")
        print "see ball at ",t
        return t != None
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
        return (math.fabs(dist[0])<=CENTER_THRESHOLD) or ((target=="yellowWall" or\
                                                           target=="purplePyramid") and\
                                                          math.fabs(dist[0])<=WALL_CENTER_THRESHOLD)
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
            self.too_far=15
        self.ir=ir2
        self.filtering=filtering
        
    '''Continuously get IR values and log them in IR list'''
    def run(self):
        if not self.filtering:
            while self.active:
                #fix threading issue
                ir_val=self.ir.getValue()
                #if self.too_far==25:
                    #print "long"
                #else:
                    #print "short"
                #print "IR=",ir_val
                self.ir_list.append(ir_val)
                #self.f.write(str(ir_val))
                #self.f.write('\n')
                #print self.ir_val
                time.sleep(0.2)
        if self.filtering:
            li=[]
            while self.active:
                for i in xrange(0,3):
                    #fix threading issue
                    ir_val=self.ir.getValue()
                    #if self.too_far==25:
                    #    print "long"
                    #else:
                    #    print "short"
                    #print "IR=",ir_val
                    self.li.append(ir_val)
                ir_val=sum(li)/3.0
                self.ir_list.append(ir_val)
                #self.f.write(str(ir_val))
                #self.f.write('\n')
                #print self.ir_val
                time.sleep(0.2)

    '''Get IR values. If filtered, gives a weighted average for noise reduction'''
    def getIRVal(self):
        if len(self.ir_list)==0 or self.ir_list[-1]==None:
            return 50
        else:
            return self.ir_list[-1]
    def __corrected(self,x):
        #given distance, return self.too_far if it's too large
        #then when anything is too large, remember it's an invalid distance
        return (x>self.too_far)*self.too_far+x*(x<=self.too_far)#10000+x
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
            return ansI
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
        #print "ADJUSTING"
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
        self.wrapper.vs.addTarget("purplePyramid")
        self.wrapper.vs.addTarget("blueWall")
        #Update this once David puts in code to look for walls.
    def stop(self):
        self.active=False


