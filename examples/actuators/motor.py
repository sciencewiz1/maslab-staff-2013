import sys
sys.path.append("../..")
import time

import arduino

ard = arduino.Arduino()
m0 = arduino.Motor(ard, 6, 52, 12)
ard.run()  # Start the Arduino communication thread

while True:
    print "forward"
    m0.setSpeed(126)
    time.sleep(1)
    print "stop"
    m0.setSpeed(0)
    time.sleep(1)
    print "backward"
    m0.setSpeed(-126)
    time.sleep(1)
    m0.setSpeed(0)
    time.sleep(1)
    break
ard.stop()

'''import sys
sys.path.append("../..")
import time

import arduino

ard = arduino.Arduino()
m0 = arduino.Motor(ard, 0, 2, 3)
ard.run()  # Start the Arduino communication thread

while True:
    m0.setSpeed(126)
    time.sleep(1)
    m0.setSpeed(0)
    time.sleep(1)
    m0.setSpeed(-126)
    time.sleep(1)
    m0.setSpeed(0)
    time.sleep(1)
'''
