from build123d import *
import math

def hpc_cw1011():
    tip_width = 0.044*IN
    cutter_width = 0.25*IN
    cutter_height = 2.375*IN/2
    angle = 90

    a = tip_width/2
    b = cutter_width/2
    c = b*math.tan(angle/360 * math.pi)

    cutter_poly = Face(Pos(0,-cutter_height,0) * Polyline([(-a,0),(a,0),(b,c),(b,cutter_height),(-b,cutter_height),(-b,c),(-a,0)]))
    cutter = revolve(cutter_poly, Axis.X)
    cutter = Pos(0,cutter_height) * cutter
    return cutter