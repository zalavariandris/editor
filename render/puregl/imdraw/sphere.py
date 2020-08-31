from OpenGL.GL import *
import numpy as np
from .helpers import buffer_offset
import math

import logging
import functools

@functools.lru_cache(maxsize=128)
def sphere_geo():
    """
    reference: [http://www.songho.ca/opengl/gl_sphere.html]
    """
    logging.debug('create sphere geometry')

    vertices = []
    normals = []
    texCoords = []

    radius = 0.5
    origin = (0,-0.5,0)
    sectorCount = 36
    stackCount = 36

    #
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

    positions = np.array(vertices, dtype=np.float32).reshape( (-1, 3))
    
    magnitudes = np.sqrt((positions ** 2).sum(-1))[..., np.newaxis]
    normals = positions/magnitudes
    positions-=origin
    uvs = np.array(texCoords, dtype=np.float32).reshape((-1,2))
    indices = np.array(indices, dtype=np.uint)
    count = indices.size
    return positions, normals, uvs, indices, count

@functools.lru_cache(maxsize=128)
def create_buffer(program):
    positions, normals, uvs, indices, count = sphere_geo()
    logging.debug("create sphere buffer")

    # create VAO
    vao = glGenVertexArrays(1)
    
    pos_vbo, uv_vbo, normal_vbo = glGenBuffers(3) # FIXME: use single vbo for positions and vertices
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
    glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
    position_location = glGetAttribLocation(program, 'position')
    glVertexAttribPointer(position_location, 3, GL_FLOAT, False, 0, buffer_offset(0))
    glEnableVertexAttribArray(position_location)

    uv_location = glGetAttribLocation(program, 'uv')
    if uv_location>=0:
        glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
        glBufferData(GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL_STATIC_DRAW)
        glVertexAttribPointer(uv_location, 2, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(uv_location)

    normal_location = glGetAttribLocation(program, 'normal')
    if normal_location is not -1:
        glBindBuffer(GL_ARRAY_BUFFER, normal_vbo)
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
        glVertexAttribPointer(normal_location, 3, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(normal_location)

    glBindBuffer(GL_ARRAY_BUFFER, 0)

    glBindVertexArray(0)

    # create EBO
    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    return vao, ebo, count


def sphere(program):
    vao, ebo, count = create_buffer(program)

    # draw sphere
    glBindVertexArray(vao)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
