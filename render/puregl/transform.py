import glm
import numpy as np


def orbit(m: glm.mat4, dx:float, dy:float):
    horizontal_axis = glm.vec3( m[0][0], m[1][0], m[2][0] )
    vertical_axis = glm.vec3(0,1,0)

    m *= glm.rotate(np.eye(4, dtype=np.float32), dy*0.006, horizontal_axis)
    m *= glm.rotate(np.eye(4, dtype=np.float32), dx*0.006, vertical_axis)

    return m
