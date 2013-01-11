from math import *
from constants import *

#returns (distance of ball, angle)
def ball_coordinates(p1,p2):
    angle1=degrees(atan(p1/(PIXELS+0.0)))
    angle2=degrees(atan(p2/(PIXELS+0.0)))
    
