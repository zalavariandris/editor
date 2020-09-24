from OpenGL.GL import *
from editor.render.puregl import program
import numpy as np


def axis(projection, view):
    prog = program.create(
        """#version 330 core
        layout (location=0) in vec3 position;
        layout (location=1) in vec3 color;
        uniform mat4 projection;
        uniform mat4 view;
        uniform mat4 model;
        
        out vec3 Color;
        void main(){
            Color = color;
            gl_Position = projection * view * model * vec4(position, 1.0);
        }
        """,
        """#version 330 core
        in vec3 Color;
        out vec4 FragColor;
        void main(){
            FragColor = vec4(Color, 1.0);
        }
        """)
    positions = np.array([
        (0,0,0), (1,0,0),
        (0,0,0), (0,1,0),
        (0,0,0), (0,0,1)
    ]).astype(np.float32)
    colors = np.array([
        (1, 0, 0), (1, 0, 0),
        (0, 1, 0), (0, 1, 0),
        (0, 0, 1), (0, 0, 1)
    ]).astype(np.float32)
    pos_vbo, col_vbo = glGenBuffers(2)
    glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
    glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
    glBindBuffer(GL_ARRAY_BUFFER, col_vbo)
    glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)

    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
    glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, None)
    glEnableVertexAttribArray(0)
    glBindBuffer(GL_ARRAY_BUFFER, col_vbo)
    glVertexAttribPointer(1, 3, GL_FLOAT, False, 0, None)
    glEnableVertexAttribArray(1)

    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)

    with program.use(prog):
        # set program
        program.set_uniform(prog, "projection", projection)
        program.set_uniform(prog, "view", view)
        program.set_uniform(prog, "model", np.eye(4))

        # draw
        glBindVertexArray(vao)
        glDrawArrays(GL_LINES, 0, 3*2)
        glBindVertexArray(0)

