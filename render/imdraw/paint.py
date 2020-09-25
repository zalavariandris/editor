import functools
from contextlib import contextmanager
from editor.render import puregl
import glm

@functools.lru_cache(maxsize=128)
def create_paint_program():
	return puregl.program.create(
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

@contextmanager
def paint(color=glm.vec3(1,1,1)):
	prog = create_paint_program()
	with puregl.program.use(prog):
		puregl.program.set_uniform(prog, "color", color)
		yield prog