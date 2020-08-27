from OpenGL.GL import *
import numpy as np
from .helpers import buffer_offset

def cube(program):
    try:
        vao = cube.vao
        ebo = cube.ebo
    except AttributeError:
        """ create flat cube
        [https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/Tutorial/Creating_3D_objects_using_WebGL]
        """
        # Create geometry
        positions = np.array([
            # Front face
            -0.5, -0.5,  0.5,
            0.5, -0.5,  0.5,
            0.5,  0.5,  0.5,
            -0.5,  0.5,  0.5,

            # Back face
            -0.5, -0.5, -0.5,
            -0.5,  0.5, -0.5,
            0.5,  0.5, -0.5,
            0.5, -0.5, -0.5,

            # Top face
            -0.5,  0.5, -0.5,
            -0.5,  0.5,  0.5,
            0.5,  0.5,  0.5,
            0.5,  0.5, -0.5,

            # Bottom face
            -0.5, -0.5, -0.5,
            0.5, -0.5, -0.5,
            0.5, -0.5,  0.5,
            -0.5, -0.5,  0.5,

            # Right face
            0.5, -0.5, -0.5,
            0.5,  0.5, -0.5,
            0.5,  0.5,  0.5,
            0.5, -0.5,  0.5,

            # Left face
            -0.5, -0.5, -0.5,
            -0.5, -0.5,  0.5,
            -0.5,  0.5,  0.5,
            -0.5,  0.5, -0.5,
        ], dtype=np.float32).reshape((-1,3))
        positions+=(0,0.5,0)

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

        print("indices.size", indices.size)

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

        # setup VAO
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

        # create ebo
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        cube.vao = vao
    finally:
        glBindVertexArray(vao)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glDrawElements(GL_TRIANGLES, 6*6, GL_UNSIGNED_INT, None)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
