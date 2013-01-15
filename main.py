import arduino, time, threading
from constants import *
from wrapper import *
from actions import *
from states import *
from wx import *
log=[]
class RobotControllerApp(Frame, threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()
    def run(self):
        self.buildGUI()
    def buildGUI(self):
        self.master=App(False)
        Frame.__init__(self,None,title="Robot Control System",size=(500,500))
        #self.control = TextCtrl(self, style=TE_MULTILINE)
        self.createWidgets()
        self.loadMainObjects()
        self.Show(True)
        self.master.MainLoop()
    def createWidgets(self):
        #create file menu
        self.filemenu=Menu()
        #add items to file menu
        self.aboutMenuItem=self.filemenu.Append(ID_ABOUT,"&About","Info About this program")
        self.runSMMenuItem=self.filemenu.Append(ID_ANY,"&Run SM","Run the StateMachine")
        self.stopSMMenuItem=self.filemenu.Append(ID_ANY,"&Pause SM","Pause the StateMachine Execution")
        self.manualControl=self.filemenu.Append(ID_ANY,"&Manual Control","Manually Control the Robot")
        #create method button bindings for menu items
        #bind method->menuItem
        #method requires arg:(self,event)
        self.Bind(EVT_MENU, self.about, self.aboutMenuItem)
        self.Bind(EVT_MENU,self.startSM,self.runSMMenuItem)
        self.Bind(EVT_MENU,self.pauseSM,self.stopSMMenuItem)
        self.Bind(EVT_CLOSE, self.OnClose)
        #create menubar
        self.menuBar=MenuBar()
        #add file menu to menubar
        self.menuBar.Append(self.filemenu,"&File")
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
        mainLabel="MASLAB 2013 Team 12 Robot Control System"
        msg="This is the GUI for the main control system of the robot for the MASLAB 2013 Competition.\n The project team included: Holden Lee, David Goehring, Melody Liu, and Roxana Mata"
        dlg=MessageDialog( self, msg,mainLabel,wx.OK)
        dlg.ShowModal()
        dlg.Destroy()
    def startSM(self,event):
        self.status.SetStatusText("Running SM...",0)
        self.sm.startSM()
    def pauseSM(self,event):
        self.status.SetStatusText("Pausing SM...",0)
        self.sm.pauseSM()
        self.status.SetStatusText("SM Paused...",0)
    def OnClose(self,event):
        #stops all threads and destroys all objects
        self.sm.stopSM()
        self.wrapper.stop()
        #delete objects
        del(self.sm)
        del(self.wrapper)
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
#wrapper.left_motor.setSpeed(-64)
#wrapper.right_motor.setSpeed(64)
sm=StateMachine(wrapper)
sm.runSM()'''
system=RobotControllerApp()
    
