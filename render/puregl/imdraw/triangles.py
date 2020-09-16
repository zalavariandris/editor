from OpenGL.GL import *
import ctypes


def triangles(prog, positions, indices, normals=None, uvs=None):
    # get locations
    pos_loc = glGetAttribLocation(prog, 'position')
    norm_loc = glGetAttribLocation(prog, 'position')
    uv_loc = glGetAttribLocation(prog, 'position')

    has_position = positions and pos_loc is not -1
    has_normal = uvs and norm_loc is not -1
    has_uv = normals and uv_loc is not -1

    # create vertex buffers
    if has_position:
        pos_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
        glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
    else:
        pos_vbo=None

    if has_normal:
        norm_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, norm_vbo)
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
    else:
        norm_vbo=None

    if has_uv:
        uv_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
        glBufferData(GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL_STATIC_DRAW)
    else:
        uv_vbo = None

    # create element buffer
    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    # create vao
    vao = glGenVertexArrays(1)

    # attach buffers to vao
    glBindVertexArray(vao)
    if pos_vbo:
        glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
        glVertexAttribPointer(pos_loc, 3, GL_FLOAT, False, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(pos_loc)

    if norm_vbo:
        glBindBuffer(GL_ARRAY_BUFFER, norm_vbo)
        glVertexAttribPointer(norm_loc, 3, GL_FLOAT, False, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(norm_loc)

    if uv_vbo:
        glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
        glVertexAttribPointer(uv_loc, 2, GL_FLOAT, False, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(uv_loc)
    glBindVertexArray(0)

    # draw
    glBindVertexArray(vao)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glDrawElements(GL_TRIANGLES, indices.size, GL_UNSIGNED_INT, None)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
    glBindVertexArray(0)

    # cleanup
    glDeleteVertexArrays(1, vao)
    glDeleteBuffers(1, ebo)
    if pos_vbo:
        glDeleteBuffers(1, pos_vbo)
    if norm_vbo:
        glDeleteBuffers(1, norm_vbo)
    if uv_vbo:
        glDeleteBuffers(1, uv_vbo)
