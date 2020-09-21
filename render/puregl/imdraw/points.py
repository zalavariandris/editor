from OpenGL.GL import *
import ctypes
import logging


def points(prog, positions):
    # get locations
    pos_loc = glGetAttribLocation(prog, 'position')

    has_position = positions and pos_loc is not -1

    # create vertex buffers
    logging.debug("create points buffers")
    if has_position:
        pos_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
        glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
    else:
        pos_vbo=None

    # create vao
    vao = glGenVertexArrays(1)

    # attach buffers to vao
    glBindVertexArray(vao)
    if pos_vbo:
        glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
        glVertexAttribPointer(pos_loc, 3, GL_FLOAT, False, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(pos_loc)

    glBindVertexArray(0)

    # draw
    glBindVertexArray(vao)
    glDrawArrays(GL_POINTS, positions.shape[0], GL_UNSIGNED_INT, None)
    glBindVertexArray(0)

    # cleanup
    glDeleteVertexArrays(1, vao)
    if pos_vbo:
        glDeleteBuffers(1, pos_vbo)
