from OpenGL.GL import *
import numpy as np


def grid(prog, size=10.9):
    # create geometry
    positions = []
    offset = int(size)/2
    for x in range(0, int(size)+1):
        positions.append((x-offset, 0, size/2))
        positions.append((x-offset, 0, -size/2))

    for y in range(0, int(size)+1):
        positions.append((size/2, 0, y-offset))
        positions.append((-size/2, 0, y-offset))

    positions = np.array(positions, dtype=np.float32)

    # create buffers
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)

    vao = glGenVertexArrays(1)

    # draw
    glBindVertexArray(vao)
    loc = glGetAttribLocation(prog, "position")
    glVertexAttribPointer(loc, 3, GL_FLOAT, False, 0, None)
    glEnableVertexAttribArray(loc)
    glDrawArrays(GL_LINES, 0, positions.size)
    glBindVertexArray(0)

