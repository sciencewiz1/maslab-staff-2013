#IR threshold: what counts as "close"?
IR_THRESHOLD = 200.0
#IR threshold: what counts as "too close"?
IR_THRESHOLD2 = 400.0
#when to stop (seconds)
STOP_TIME = 180
#check these signs
LEFT_FORWARD=-96
RIGHT_FORWARD=75
LEFT_BACK=96
RIGHT_BACK=-75
LEFT_RIGHT_RATIO=1.28
#what are we looking for?
BALL_MODE=0
PYRAMID_MODE=1
#turn speed (degrees/s)
#experimentally find this.
#later, preferably change this to dynamic control
TURN_SPEED=1/90.0
#color
RED=0
GREEN=1
#direction
LEFT=-1
RIGHT=1

CENTER_THRESHOLD=200

#Right now I randomly estimate 1 degree/4 pixels, change this to something more
#exact later
#in units of (motor speed)/(angle in degrees).
#motor speed is -126 to 126
TURN_KP = 1
#in units of (motor speed)/(angle in degrees*s)
TURN_KI = 0
#in units of (motor speed s)/(angle in degrees)
TURN_KD = 0


#angle in degrees between straight forward and furthest right the camera can see
CAMERA_HALF_WIDTH=31
#half the number of pixels horizontally
PIXELS=250

#regression line for IR to distance
SLOPE=-2177.305428
Y_INTERCEPT=-0.84208

