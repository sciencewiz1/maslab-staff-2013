#IR threshold: what counts as "close"?
IR_THRESHOLD = 180.0
#IR threshold: what counts as "too close"?
IR_THRESHOLD2 = 300.0
#when to go for the wall
WALL_TIME = 120
#when to stop (seconds)
STOP_TIME = 180
#for testing
#check these signs
LEFT_SIGN=-1
RIGHT_SIGN=1
ROLLER_SIGN=1
'''!!!!!!!!!!'''
LEFT_TURN=LEFT_SIGN*48
RIGHT_TURN=RIGHT_SIGN*68
LEFT_FORWARD=LEFT_SIGN*64
RIGHT_FORWARD=RIGHT_SIGN*91
LEFT_BACK=-LEFT_SIGN*64
RIGHT_BACK=-RIGHT_SIGN*91
MAX_LEFT=LEFT_SIGN*126
MAX_RIGHT=RIGHT_SIGN*126
LEFT_RIGHT_RATIO=64.0/91
#what are we looking for?
BALL_MODE=0
WALL_MODE=1
#turn speed (degrees/s)
#experimentally find this.
#later, preferably change this to dynamic control
TURN_SPEED=50.0
#color
RED=0
GREEN=1
#direction
LEFT=-1
RIGHT=1

CENTER_THRESHOLD=100

#Right now I randomly estimate 1 degree/4 pixels, change this to something more
#exact later
#in units of (motor speed)/(angle in degrees).
#motor speed is -126 to 126
TURN_KP = .8
#in units of (motor speed)/(angle in degrees*s)
TURN_KI = .2
#in units of (motor speed s)/(angle in degrees)
TURN_KD = .1


#angle in degrees between straight forward and furthest right the camera can see
CAMERA_HALF_WIDTH=31
#half the number of pixels horizontally
PIXELS=250

#regression line for IR to distance
#obstacle distance = Y_INTERCEPT+SLOPE*1/self.getIRVal()
SLOPE=-2177.305428
Y_INTERCEPT=-0.84208
#regression line for IR to distance
SLOPE=-2177.305428
Y_INTERCEPT=-0.84208

DEBUG=1
#set to 1 when debugging, 0 otherwise

#output to laptop
FRONT_DIST=0
LEFT_DIST=1
RIGHT_DIST=2
LEFT_BUMP=4
RIGHT_BUMP=5
COMPASS=10
X_ACC=11
Y_ACC=12
Z_ACC=13
#input to arduino
ROLLER_MOTOR=20
LEFT_MOTOR=21
RIGHT_MOTOR=22
