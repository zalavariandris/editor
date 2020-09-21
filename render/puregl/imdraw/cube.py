from OpenGL.GL import *
import numpy as np
from .helpers import buffer_offset
import logging
import functools


from .. import geo


@functools.lru_cache(maxsize=128)
def cube_buffer(locations, flip=False):
    logging.debug("create cube buffer".format())
    positions, normals, uvs, indices = geo.cube(flip=flip)
    position_location, uv_location, normal_location = locations
    count = indices.size

    # setup VAO
    vao = glGenVertexArrays(1)
    
    pos_vbo, uv_vbo, normal_vbo = glGenBuffers(3)  # FIXME: use single vbo for positions and vertices
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
    glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)

    # position_location = glGetAttribLocation(program, 'position')
    glVertexAttribPointer(position_location, 3, GL_FLOAT, False, 0, buffer_offset(0))
    glEnableVertexAttribArray(position_location)

    # uv_location = glGetAttribLocation(program, 'uv')
    if uv_location >= 0:
        glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
        glBufferData(GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL_STATIC_DRAW)
        glVertexAttribPointer(uv_location, 2, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(uv_location)

    # normal_location = glGetAttribLocation(program, 'normal')
    if normal_location is not -1:
        glBindBuffer(GL_ARRAY_BUFFER, normal_vbo)
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
        glVertexAttribPointer(normal_location, 3, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(normal_location)

    glBindBuffer(GL_ARRAY_BUFFER, 0)

    glBindVertexArray(0)

    # create ebo
    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    return vao, ebo, count


def cube(program, flip=False):
    locations = tuple(glGetAttribLocation(program, name) for name in ("position", 'uv', 'normal'))
    vao, ebo, count = cube_buffer(locations, flip=flip)

    # draw
    glBindVertexArray(vao)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glDrawElements(GL_TRIANGLES, 6*6, GL_UNSIGNED_INT, None)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
