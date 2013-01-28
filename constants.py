#IR threshold: what counts as "close"?
CLOSE = 6.0
#IR threshold: what counts as "too close"?
TOO_CLOSE = 3.0
#when to go for the wall
WALL_TIME = 120
#when to stop (seconds)
STOP_TIME = 180
#for testing
#check these signs
LEFT_SIGN=-1
RIGHT_SIGN=-1
ROLLER_SIGN=1
ROLLER_ANGLE=120
ROLLER_STOP=106
'''!!!!!!!!!!'''
LEFT_TURN=LEFT_SIGN*20
RIGHT_TURN=RIGHT_SIGN*20
LEFT_FORWARD=LEFT_SIGN*80
RIGHT_FORWARD=RIGHT_SIGN*80
LEFT_BACK=-LEFT_SIGN*80
RIGHT_BACK=-RIGHT_SIGN*80
MAX_LEFT=LEFT_SIGN*126
MAX_RIGHT=RIGHT_SIGN*126
LEFT_RIGHT_RATIO=1
#what are we looking for?
BALL_MODE=0
WALL_MODE=1
#turn speed (degrees/s)
#experimentally find this.
#later, preferably change this to dynamic control
TURN_SPEED=50.0
#color
RED="redBall"
GREEN="greenBall"
#direction
LEFT=-1
RIGHT=1

CENTER_THRESHOLD=200

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
PIXELS=240
Y_PIXELS=120

#regression line for IR to distance
#obstacle distance = Y_INTERCEPT+SLOPE*1/self.getIRVal()
SLOPE=7611.1
Y_INTERCEPT=-6.95122
#regression line for IR to distance
LONG_SLOPE=14757.89
LONG_Y_INTERCEPT=-11.1283

DEBUG=1
#set to 1 when debugging, 0 otherwise

#output to laptop
FRONT_DIST=0
FRONT_DIST2=1
LEFT_DIST=2
RIGHT_DIST=3
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
