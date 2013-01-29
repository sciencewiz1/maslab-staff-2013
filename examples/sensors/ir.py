import time
import sys
sys.path.append("../..")

import arduino

# Example code to run an IR sensor. Turns on the LED
# at digital pin 13 when the IR sensor detects anything within
# a certain distance.

THRESH = 200.0  # Experimentally chosen

ard = arduino.Arduino()  # Create the Arduino object
a0 = arduino.AnalogInput(ard, 0)  # Create an analog sensor on pin A0
a1 = arduino.AnalogInput(ard, 1)  
ard.run()  # Start the thread which communicates with the Arduino

start_time=time.time()
# Main loop -- check the sensor and update the digital output
while time.time()<start_time+10:
    ir_val = a0.getValue() # Note -- the higher value, the *closer* the dist
    ir_val2 = a1.getValue()
    print ir_val, ir_val2 
    time.sleep(0.1)
ard.stop()
