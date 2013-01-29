import sys
sys.path.append("../..")
import time

import arduino

# A simple example of using the arduino library to
# control a servo.

ard = arduino.Arduino()
servo = arduino.Servo(ard, 42)  # Create a Servo object
ard.run()  # Run the Arduino communication thread

#while True:
# Sweep the servo back and forth
for i in range(0, 180, 10):
    servo.setAngle(i)
    print "Angle", i
    time.sleep(5)
for i in range(180, 0, -10):
    servo.setAngle(i)
    print "Angle", i
    time.sleep(5)

