<<<<<<< HEAD
import sys
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
=======
import sys
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
>>>>>>> d491236668d75c169a73fb21f486db0b29a68de9
