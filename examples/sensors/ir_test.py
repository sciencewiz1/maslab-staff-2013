import time
import sys
sys.path.append("../..")

import arduino

# Example code to run an IR sensor. Turns on the LED
# at digital pin 13 when the IR sensor detects anything within
# a certain distance.

#THRESH = 200.0  # Experimentally chosen

ard = arduino.Arduino()  # Create the Arduino object
a0 = arduino.AnalogInput(ard, 0)  # Create an analog sensor on pin A0
a1 = arduino.AnalogInput(ard, 1)  
ard.run()  # Start the thread which communicates with the Arduino

# Main loop -- check the sensor and update the digital output
a=int(raw_input("Inches:"))
while a!=0:
    start_time=time.time()
    while time.time()<=start_time+5:
        ir_val = a0.getValue() # Note -- the higher0 value, the *closer* the dist
        ir_val1 = a1.getValue()
        #print time.time()-start_time
        print ir_val, ir_val1#, ir_val >= THRESH
        time.sleep(0.1)
    a=int(raw_input("Inches:"))
ard.stop()
