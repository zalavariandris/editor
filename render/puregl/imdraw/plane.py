from OpenGL.GL import *
import numpy as np
from .helpers import buffer_offset

def plane(program):
    positions = np.array(
        # positions        # texture Coords
        [(-1.0, 0.0, 1.0),
        (-1.0,  0.0, -1.0),
        ( 1.0,  0.0, 1.0),
        ( 1.0,  0.0, -1.0)],
        dtype=np.float32
    )
    positions*=(3, 1, 3)

    uvs = np.array(
        # positions        # texture Coords
        [(0.0, 1.0),
        (0.0, 0.0),
        (1.0, 1.0),
        (1.0, 0.0)],
        dtype=np.float32
    )

    normals = np.array(
        # positions        # texture Coords
        [(0.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 1.0, 0.0)],
        dtype=np.float32
    )

    # setup VAO
    vao = glGenVertexArrays(1)

    pos_vbo, uv_vbo, normal_vbo = glGenBuffers(3) # FIXME: use single vbo for positions and vertices
    glBindVertexArray(vao)

    position_location = glGetAttribLocation(program, 'position')
    glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
    glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
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

    glBindVertexArray(vao)
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
    glBindVertexArray(0)
