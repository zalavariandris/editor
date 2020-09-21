from OpenGL.GL import *
import numpy as np
from editor.render.puregl import program
from editor.render import glsl
import logging

def grid(projection, view):
    size = 10
    # create geometry
    # ---------------
    logging.debug("create grid geometry")
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
    logging.debug("create grid buffers")
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)

    vao = glGenVertexArrays(1)

    # create program
    logging.debug("create grid program")
    prog = program.create(
        """#version 330 core
        layout (location=0) in vec3 position;
        uniform mat4 projection;
        uniform mat4 view;

        void main(){
            gl_Position = projection * view * vec4(position, 1.0);
        }
        """,
        """#version 330 core
        out vec4 FragColor;
        void main(){
            FragColor = vec4(0.5,0.5,0.5,1);
        }
        """)

    # draw
    with program.use(prog):
        program.set_uniform(prog, "projection", projection)
        program.set_uniform(prog, "view", view)
        glBindVertexArray(vao)
        loc = glGetAttribLocation(prog, "position")
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, 0, None)
        glEnableVertexAttribArray(loc)
        glDrawArrays(GL_LINES, 0, positions.size)
        glBindVertexArray(0)

