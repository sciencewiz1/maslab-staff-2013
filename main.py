import arduino, time, threading
from constants import *
from wrapper import *
from actions import *
from states import *
from wx import *
import sys
import pickle

class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)

class RobotControllerApp(Frame, threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.sm=None
        self.wrapper=None
        self.writeLog()
        self.start()
    def run(self):
        self.buildGUI()
    def buildGUI(self):
        self.master=App(False)
        Frame.__init__(self,None,title="Robot Control System",size=(500,500))
        #self.control = TextCtrl(self, style=TE_MULTILINE)
        self.mainLabel="MASLAB 2013 Team 12 Robot Control System"
        self.createWidgets()
        self.loadMainObjects()
        self.Show(True)
        self.master.MainLoop()
    def createWidgets(self):
        #create menus
        self.filemenu=Menu()
        self.options=Menu()
        #add items to file menu
        self.runSMMenuItem=self.filemenu.Append(ID_ANY,"&Run SM","Run the StateMachine")
        self.stopSMMenuItem=self.filemenu.Append(ID_ANY,"&Pause SM","Pause the StateMachine Execution")
        self.manualControlMenuItem=self.filemenu.Append(ID_ANY,"&Manual Control","Manually Control the Robot")
        self.aboutMenuItem=self.filemenu.Append(ID_ABOUT,"&About","Info About this program")
        #add items to options
        self.changeCameraMenuItem=self.options.Append(ID_ANY,"&Change Camera","Change which camera the Vision System uses.")
        #create method button bindings for menu items
        #bind method->menuItem
        #method requires arg:(self,event)
        self.Bind(EVT_MENU, self.about, self.aboutMenuItem)
        self.Bind(EVT_MENU,self.startSM,self.runSMMenuItem)
        self.Bind(EVT_MENU,self.pauseSM,self.stopSMMenuItem)
        self.Bind(EVT_MENU,self.activateManualControl,self.manualControlMenuItem)
        self.Bind(EVT_MENU,self.changeCameraNumber,self.changeCameraMenuItem)
        self.Bind(EVT_CLOSE, self.OnClose)
        #create menubar
        self.menuBar=MenuBar()
        #add file menu to menubar
        self.menuBar.Append(self.filemenu,"&File")
        self.menuBar.Append(self.options,"&Options")
        #set status bar
        self.SetMenuBar(self.menuBar)
        self.status=self.CreateStatusBar(style=0)
        self.status.SetFieldsCount(2)
        self.status.SetStatusText("Loading...",1)
    def loadMainObjects(self):
        self.status.SetStatusText("Loading Wrapper...",0)
        self.wrapper=Wrapper()
        self.status.SetStatusText("Loading StateMachine...",0)
        self.sm=StateMachine(self.wrapper)
        portOpened,port=self.wrapper.connected()
        if portOpened:
            self.SetStatusText("Connected to Arduino on port: "+str(port),1)
        else:
            self.SetStatusText("Failed to connect, please plug in the Arduino!",1)
        self.status.SetStatusText("System Ready...",0)
    def about(self,event):
        msg="This is the GUI for the main control system of the robot for the MASLAB 2013 Competition.\n The project team included: Holden Lee, David Goehring, Melody Liu, and Roxana Mata"
        dlg=MessageDialog( self, msg,self.mainLabel,wx.OK)
        dlg.ShowModal()
        dlg.Destroy()
    def changeCameraNumber(self,event):
        cameraNumDialog = TextEntryDialog(None, "Please enter the camera index.", 'Vision System: Change Camera Number', '')
        if cameraNumDialog.ShowModal() == wx.ID_OK:
            cameraNum=cameraNumDialog.GetValue()
            try:
                cameraNum=int(cameraNum)
                self.wrapper.changeCameraNumber(cameraNum)
                msg="Camera Number changed to: "+str(cameraNum)
                dlg=MessageDialog(self,msg,self.mainLabel,wx.OK)
                dlg.ShowModal()
            except:
                msg="Invalid Camera Number"
                dlg=MessageDialog( self, msg,self.mainLabel,wx.OK)
                dlg.ShowModal()
    def activateManualControl(self,event):
        if not self.wrapper.manualControlCheck():
            self.pauseSM(event)
            self.wrapper.manualOverride()
            msg="Manual override started!"
            dlg=MessageDialog(self,msg,self.mainLabel,wx.OK)
            dlg.ShowModal()
        else:
            msg="You are already in manual override mode!"
            dlg=MessageDialog(self,msg,self.mainLavel,wx.OK)
            dlg.ShowModal()
    def startSM(self,event):
        if self.wrapper.manualControlCheck():
            self.wrapper.returnToSMMode()
        self.status.SetStatusText("Running SM...",0)
        self.wrapper.resetRoller()
        self.sm.startSM()
    def pauseSM(self,event):
        self.status.SetStatusText("Pausing SM...",0)
        self.sm.pauseSM()
        self.wrapper.turnMotorsOff()
        self.status.SetStatusText("SM Paused...",0)
    def writeLog(self):
        self.original=sys.stdout
        self.fsock=open("log.txt",'w')
        sys.stdout=sys.stdout = Tee(sys.stdout, self.fsock)
    def OnClose(self,event):
        #stops all threads and destroys all objects
        self.sm.stopSM()
        self.wrapper.stop()
        #delete objects
        del(self.sm)
        del(self.wrapper)
        #write log
        sys.stdout=self.original
        self.fsock.close()
        #destroy GUI
        #instance is a frame
        self.master.ExitMainLoop() #self.master.Exit()   # or wx.GetApp().ExitMainLoop()
        
        
        

"""Note: I created specific actions as subclasses of Action, though an
alternative is to make objects of type Action"""

class StateMachine(threading.Thread):
    def __init__(self,wrap):
        threading.Thread.__init__(self)
        #create a wrapper for arduino that handles all I/O
        self.wrapper=wrap
        self.active=True
        self.pause=False
        self.state=None
        #self.arduino=ard
    def run(self):
        #set the starting state
        self.state=TurnAndLook(self.wrapper)
        print "set starting state"
        #in the future, categorize states more sophisticatedly (ex. explore)
        while True:
            if not self.pause:
                #does whatever it's supposed to in this state and then transitions
                self.state=self.state.run()
                print "SM next state"
                #repeat indefinitely
                #in the future add a timer, stop when time over threshold
                #add time.sleep to allow other threads to execute
                time.sleep(1)
    def startSM(self):
        if not self.isAlive():
            self.start()
        self.active=True
        self.pause=False
    def pauseSM(self):
        self.pause=True
    def stopSM(self):
        self.pause=True
        self.active=False
        

'''ard = arduino.Arduino()
wrapper=Wrapper(ard)
#wrapper.left_motor.setSpeed(LEFT_FORWARD)
#wrapper.right_motor.setSpeed(RIGHT_FORWARD)
sm=StateMachine(wrapper)
sm.runSM()'''
system=RobotControllerApp()
    
