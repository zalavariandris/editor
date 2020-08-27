import time
import contextlib
import numpy as np
import glm

# helpers
def orbit(inputMatrix, dx, dy):
    horizontalAxis = glm.vec3( inputMatrix[0][0], inputMatrix[1][0], inputMatrix[2][0] )
    verticalAxis = glm.vec3(0,1,0)

    inputMatrix *= glm.rotate(np.eye(4, dtype=np.float32), dy*0.006, horizontalAxis)
    inputMatrix *= glm.rotate(np.eye(4, dtype=np.float32), dx*0.006, verticalAxis)

    return inputMatrix

def box(width=1, height=1, length=1, origin=(0,0, 0)):
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
    positions-=origin

    normals = np.array([
         0.0,  0.0,  1.0, # Front face
         0.0,  0.0, -1.0, # Back face
         0.0,  1.0,  0.0, # Top face
         0.0, -1.0,  0.0, # Bottom face
         1.0,  0.0,  0.0, # Right face
        -1.0,  0.0,  0.0, # Left face
    ], dtype=np.float32).reshape((-1,3)).repeat(4, axis=0)



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
    ], dtype=np.float32).reshape(-1,2)

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
        'normals': normals,
        'indices':   indices,
        'uvs':       uvs,
        'colors':    colors
        }

def plane(width=1, length=1, origin=(0,0)):
    # Create geometry
    positions = np.array([
        -1, 0,  1,
        1, 0,  1,
        1, 0, -1,
        -1, 0, -1,
    ], dtype=np.float32).reshape((-1,3))
    positions/=2, 2, 2
    positions*=width, 1.0, length
    positions[:,0:2]-=origin

    normals = np.repeat((0,1,0), 4).astype(np.float32)

    indices = np.array([
        0,1,2,
        0,2,3
    ], dtype=np.uint).reshape((-1,3))

    uvs = np.array([
        0,  0, 
        1,  0,
        1,  1,
        0,  1,
    ],dtype=np.float32).reshape((-1,2))

    colors = np.array([
         1, 1, 1, 1,
         1, 1, 1, 1,
         1, 1, 1, 1,
         1, 1, 1, 1
    ],dtype=np.float32).reshape((-1,4))

    return {
        'positions': positions,
        'normals': normals,
        'indices':   indices,
        'uvs':       uvs,
        'colors':    colors
        }

import math

import math
def sphere(radius=0.5, origin=(0,0.5,0)):
    """
    reference: [http://www.songho.ca/opengl/gl_sphere.html]
    """
    vertices = []
    normals = []
    texCoords = []

    sectorCount = 8
    stackCount = 8

    sectorStep = 2 * math.pi / sectorCount
    stackStep = math.pi / stackCount

    lengthInv = 1/radius

    for i in range(0, stackCount+1):
        stackAngle = math.pi / 2 - i * stackStep;        # starting from pi/2 to -pi/2
        xy = radius * math.cos(stackAngle);             # r * cos(u)
        y = radius * math.sin(stackAngle);              # r * sin(u)

        # add (sectorCount+1) vertices per stack
        # the first and last vertices have same position and normal, but different tex coords
        for j in range(0, sectorCount+1):
            sectorAngle = j * sectorStep;           # starting from 0 to 2pi

            # vertex position (x, y, z)
            x = xy * math.cos(sectorAngle)             # r * cos(u) * cos(v)
            z = xy * math.sin(sectorAngle)             # r * cos(u) * sin(v)
            vertices.append(x)
            vertices.append(y)
            vertices.append(z)

            # normalized vertex normal (nx, ny, nz)
            nx = x * lengthInv
            ny = y * lengthInv
            nz = z * lengthInv
            normals.append(nx)
            normals.append(ny)
            normals.append(nz)

            # vertex tex coord (s, t) range between [0, 1]
            s = j / sectorCount
            t = i / stackCount
            texCoords.append(s)
            texCoords.append(t)

    indices = []
    for i in range(0, stackCount):
        k1 = i * (sectorCount + 1)     # beginning of current stack
        k2 = k1 + sectorCount + 1      # beginning of next stack

        for j in range(0, sectorCount):
            # 2 triangles per sector excluding first and last stacks
            # k1 => k2 => k1+1
            if i != 0:
                indices.append(k1 + 1)
                indices.append(k2)
                indices.append(k1)
                
            # k1+1 => k2 => k2+1
            if i != (stackCount-1):
                indices.append(k2 + 1)
                indices.append(k2)
                indices.append(k1 + 1)
                
            k1+=1
            k2+=1

    # colors = np.zeros( (len(vertices)/3*4) )
    positions = np.array(vertices, dtype=np.float32).reshape( (-1, 3))
    magnitudes = np.sqrt((positions ** 2).sum(-1))[..., np.newaxis]
    normals = positions/magnitudes
    positions-=origin
    return {
        'positions': positions,
        'normals': normals,
        'indices': np.array(indices, dtype=np.uint),
        'uvs': np.array(texCoords, dtype=np.float32).reshape((-1,2)),
        'colors': np.random.uniform(0,1, (len(vertices)//3, 4) ).astype(np.float32)
    }

def buffer_offset(itemsize):
    import ctypes
    return ctypes.c_void_p(itemsize)