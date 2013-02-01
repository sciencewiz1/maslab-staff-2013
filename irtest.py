import wrapper,time
from constants import *
w=wrapper.Wrapper()
w.ard.run()
w.ir_module.start()
w.ir_module2.start()
w.left_ir_module.start()
w.right_ir_module.start()
start_time=time.time()
while time.time()<=start_time+20:
    if len(w.ir_module.ir_list)>0:
        print w.ir_module.ir_list[-1]
    if len(w.ir_module2.ir_list)>0:
        print w.ir_module2.ir_list[-1]
    print w[FRONT_DIST],w[FRONT_DIST2]
    print w.stuck()
    time.sleep(0.2)
w.ard.stop()
