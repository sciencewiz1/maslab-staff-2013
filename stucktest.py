from wrapper import *
import time
w=Wrapper()
w.ard.run()
w.ir_module.start()
w.ir_module2.start()
start_time=time.time()
while time.time()<=start_time+15:
    print "IR: ", w.ir_module.getIRVal(),w.ir_module2.getIRVal()
    print "Dist: ",w[FRONT_DIST],w[FRONT_DIST2]
    print "Stuckness: ",w.stuck()
w.stop()
