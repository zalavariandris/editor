import time
import contextlib
import numpy as np
import glm

@contextlib.contextmanager
def profile(name, disabled=False):
    starttime = time.time()
    yield
    endtime = time.time()
    deltatime = endtime-starttime
    if not disabled:
        print("{} {:4.0} fps".format(name, 1.0/deltatime if deltatime>0 else float('inf')))

# helpers
def orbit(inputMatrix, dx, dy):
    horizontalAxis = glm.vec3( inputMatrix[0][0], inputMatrix[1][0], inputMatrix[2][0] )
    verticalAxis = glm.vec3(0,1,0)

    inputMatrix *= glm.rotate(np.eye(4, dtype=np.float32), dy*0.006, horizontalAxis)
    inputMatrix *= glm.rotate(np.eye(4, dtype=np.float32), dx*0.006, verticalAxis)

    return inputMatrix

def box(width=1, height=1, length=1, origin=(0,0)):
    """ create flat cube
    [https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/Tutorial/Creating_3D_objects_using_WebGL]
    """
    # Create geometry
    positions = np.array([
        # Front face
        -1.0, -1.0,  1.0,
        1.0, -1.0,  1.0,
        1.0,  1.0,  1.0,
        -1.0,  1.0,  1.0,

        # Back face
        -1.0, -1.0, -1.0,
        -1.0,  1.0, -1.0,
        1.0,  1.0, -1.0,
        1.0, -1.0, -1.0,

        # Top face
        -1.0,  1.0, -1.0,
        -1.0,  1.0,  1.0,
        1.0,  1.0,  1.0,
        1.0,  1.0, -1.0,

        # Bottom face
        -1.0, -1.0, -1.0,
        1.0, -1.0, -1.0,
        1.0, -1.0,  1.0,
        -1.0, -1.0,  1.0,

        # Right face
        1.0, -1.0, -1.0,
        1.0,  1.0, -1.0,
        1.0,  1.0,  1.0,
        1.0, -1.0,  1.0,

        # Left face
        -1.0, -1.0, -1.0,
        -1.0, -1.0,  1.0,
        -1.0,  1.0,  1.0,
        -1.0,  1.0, -1.0,
    ], dtype=np.float32).reshape((-1,3))

    positions/=2, 2, 2
    positions*=width, height, length
    positions[:,0:2]-=origin


    indices = np.array([
        0,  1,  2,      0,  2,  3,    # front
        4,  5,  6,      4,  6,  7,    # back
        8,  9,  10,     8,  10, 11,   # top
        12, 13, 14,     12, 14, 15,   # bottom
        16, 17, 18,     16, 18, 19,   # right
        20, 21, 22,     20, 22, 23,   # left
    ], dtype=np.uint).reshape((-1,3))

    uvs = np.array([
       # Front
        0.0,  0.0,
        1.0,  0.0,
        1.0,  1.0,
        0.0,  1.0,
        # Back
        0.0,  0.0,
        1.0,  0.0,
        1.0,  1.0,
        0.0,  1.0,
        # Top
        0.0,  0.0,
        1.0,  0.0,
        1.0,  1.0,
        0.0,  1.0,
        # Bottom
        0.0,  0.0,
        1.0,  0.0,
        1.0,  1.0,
        0.0,  1.0,
        # Right
        0.0,  0.0,
        1.0,  0.0,
        1.0,  1.0,
        0.0,  1.0,
        # Left
        0.0,  0.0,
        1.0,  0.0,
        1.0,  1.0,
        0.0,  1.0,
    ], dtype=np.float32)

    colors = np.repeat(np.array([
        [1.0,  1.0,  1.0,  1.0],    # Front face: white
        [1.0,  0.0,  0.0,  1.0],    # Back face: red
        [0.0,  1.0,  0.0,  1.0],    # Top face: green
        [0.0,  0.0,  1.0,  1.0],    # Bottom face: blue
        [1.0,  1.0,  0.0,  1.0],    # Right face: yellow
        [1.0,  0.0,  1.0,  1.0],    # Left face: purple
    ]), 4, axis=0).astype(np.float32)

    colors = np.repeat(np.array([
        (1.0,  1.0,  1.0,  1.0)
    ]), 24, axis=0).astype(np.float32)

    return {
        'positions': positions,
        'indices':   indices,
        'uvs':       uvs,
        'colors':    colors
        }

def plane(width=1, length=1, origin=(0,0)):
    # Create geometry
    positions = np.array([
        -1, 0, -1,
         1, 0, -1,
         1, 0,  1,
        -1, 0,  1
    ], dtype=np.float32).reshape((-1,3))
    positions/=2, 2, 2
    positions*=width, 1.0, length
    positions[:,0:2]-=origin

    indices = np.array([
        0,2,1,
        0,3,2
    ], dtype=np.uint).reshape((-1,3))

    uvs = np.array([
         0,  0,
         0,  1,
         1,  1,
         1,  0,
    ],dtype=np.float32).reshape((-1,2))

    colors = np.array([
         1, 1, 1, 1,
         1, 1, 1, 1,
         1, 1, 1, 1,
         1, 1, 1, 1
    ],dtype=np.float32).reshape((-1,4))

    return {
        'positions': positions,
        'indices':   indices,
        'uvs':       uvs,
        'colors':    colors
        }