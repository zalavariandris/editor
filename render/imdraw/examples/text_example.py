from editor.render import imdraw, puregl
from OpenGL.GL import *
import numpy as np
import glm
from viewer import Viewer
import time
import sys

def draw_text(prog, txt):
    print("draw text")

viewer = Viewer()
@viewer.event
def on_setup():
    vendor = glGetString(GL_VENDOR)
    renderer = glGetString(GL_RENDERER)
    print(sys.executable)
    print(vendor, renderer)
    global prog
    prog = puregl.program.create(
    """#version 330 core
    layout (location=0) in vec3 position;
    uniform mat4 projection;
    uniform mat4 view;
    uniform mat4 model;

    void main(){
        gl_Position = projection * view * model * vec4(position, 1);
    }
    """,
    """#version 330 core
    out vec4 FragColor;
    uniform float opacity = 1.0;
    uniform vec3 color = vec3(1,1,1);
    void main(){
        FragColor = vec4(color, opacity);
    }
    """)

t0 = time.time()

@viewer.event
def on_draw():
    global t0
    with puregl.program.use(prog):
        puregl.program.set_uniform(prog, 'projection', glm.ortho(-1,1,-1,1,-1,1))
        puregl.program.set_uniform(prog, 'view', np.eye(4))
        puregl.program.set_uniform(prog, 'model', np.eye(4))
        puregl.program.set_uniform(prog, 'color', np.random.uniform(0,1,(3,)))

        positions = np.random.uniform(-1,1,(10, 3)).astype(np.float32)
        draw_text(prog, "Hello my Proggy clean bitmap font")
        imdraw.lines(prog, positions)
        t1 = time.time()
        # print("{:.0f}fps".format(1/(t1-t0)))
        t0=t1

viewer.start()
