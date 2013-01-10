import arduino
import sys
sys.path.append("../..")
import time

class ArduinoWrapper:
    def __init__(self):
        #board setup
        self.ard = arduino.Arduino() 
        self.irSensor = arduino.AnalogInput(self.ard, 0)
        self.left = arduino.Motor(self.ard, 0, 2, 3)
        self.right = arduino.Motor(self.ard, 0, 2, 3) 
        self.ard.run()
        #getValue
        #setSpeed        
    def manualOverride(self,cmd,speed=126):
        cmds={"l":(speed,-speed,"Left"),"r":(-speed,speed,"Right"),"f":(speed,speed,"Forward"),"b":(-speed,-speed,"Backward"),"s":(0,0)}
        leftSpeed,rightSpeed,cmdName=cmds[cmd]
        time.sleep(1)
        self.left.setSpeed(left)
        self.right.setSpeed(right)
        print "Moving "+cmdName
control=ArduinoWrapper()
while True:
    cmd=raw_input("Enter command:")
    control.manualOverride(str(cmd))
