import time
import sys
sys.path.append("../..")

import arduino

# Example code to run an IR sensor. Turns on the LED
# at digital pin 13 when the IR sensor detects anything within
# a certain distance.

#THRESH = 200.0  # Experimentally chosen

ard = arduino.Arduino()  # Create the Arduino object
a0 = arduino.AnalogInput(ard, 1)  # Create an analog sensor on pin A0
ard.run()  # Start the thread which communicates with the Arduino

# Main loop -- check the sensor and update the digital output
start_time=time.time()
while time.time()-start_time<=10:
    ir_val = a0.getValue() # Note -- the higher value, the *closer* the dist
    #print time.time()-start_time
    print ir_val#, ir_val >= THRESH
    time.sleep(0.1)
