# A simple example that set up an IMU and prints out the raw values received from it
import sys
sys.path.append("../..")
import time
import arduino

ard = arduino.Arduino()
imu = arduino.IMU(ard)
ard.run()

start_time=time.time()
while time.time()-start_time<=10:
    print imu.getRawValues()
    time.sleep(0.05)
ard.cleanup()
ard.stop()
