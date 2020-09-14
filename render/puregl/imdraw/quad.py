from OpenGL.GL import *
import numpy as np
from .helpers import buffer_offset

import logging
import functools


@functools.lru_cache(maxsize=128)
def quad_geo():
    logging.debug("create quad geo")
    positions = np.array(
        [(-1.0, +1.0, 0.0),
         (-1.0, -1.0, 0.0),
         (+1.0, +1.0, 0.0),
         (+1.0, -1.0, 0.0)],
        dtype=np.float32
    )

    uvs = np.array(
        [(0.0, 1.0),
         (0.0, 0.0),
         (1.0, 1.0),
         (1.0, 0.0)],
        dtype=np.float32
    )

    return positions, uvs


@functools.lru_cache(maxsize=128)
def create_buffer(program):
    logging.debug("create quad buffer")
    positions, uvs = quad_geo()

    # setup VAO
    vao = glGenVertexArrays(1)

    pos_vbo, uv_vbo = glGenBuffers(2)  # FIXME: use single vbo for positions and vertices
    glBindVertexArray(vao)

    position_location = glGetAttribLocation(program, 'position')
    if position_location >= 0:
        glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
        glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
        glVertexAttribPointer(position_location, 3, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(position_location)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
    else:
        logging.warning("no 'position' attribute")

    uv_location = glGetAttribLocation(program, 'uv')
    if uv_location>=0:
        glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
        glBufferData(GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL_STATIC_DRAW)
        glVertexAttribPointer(uv_location, 2, GL_FLOAT, False, 0, buffer_offset(0))
        glEnableVertexAttribArray(uv_location)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
    else:
        logging.warning("no 'uv' attribute")

    glBindVertexArray(0)

    return vao


def quad(program):
    vao = create_buffer(program)

    # draw
    glBindVertexArray(vao)
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
    glBindVertexArray(0)
