import sys
sys.path.append("../..")
import time

import arduino

# A simple example of using the arduino library to
# control a servo.

ard = arduino.Arduino()
servo = arduino.Servo(ard, 49)  # Create a Servo object
ard.run()  # Run the Arduino communication thread

#while True:
# Sweep the servo back and forth
servo.setAngle(90)
time.sleep(5)
i=90
while i!=999:
    servo.setAngle(i)
    i=int(raw_input("ANGLE:"))
ard.stop()
#print "set to 90"
#servo.setAngle(90)
#time.sleep(5)
#print "set to 0"
#servo.setAngle(0)
#ard.stop()
#for i in range(0, 180, 10):
#    servo.setAngle(i)
#    print "Angle", i
#    time.sleep(5)
#for i in range(180, 0, -10):
#    servo.setAngle(i)
#    print "Angle", i
#    time.sleep(5)

