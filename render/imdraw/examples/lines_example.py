from editor.render import imdraw, puregl
from OpenGL.GL import *
import glfw
import numpy as np
import glm
import time
glfw.init()
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
window = glfw.create_window(1280, 720, "Lines example", None, None)

glfw.make_context_current(window)
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
positions = np.random.uniform(-1,1,(10, 3)).astype(np.float32)
print(positions)
while not glfw.window_should_close(window):
    glClearColor(0,0,0,1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)

    with puregl.program.use(prog):
    	puregl.program.set_uniform(prog, 'projection', glm.ortho(-1,1,-1,1,-1,1))
    	puregl.program.set_uniform(prog, 'view', np.eye(4))
    	puregl.program.set_uniform(prog, 'model', np.eye(4))
    	puregl.program.set_uniform(prog, 'color', np.random.uniform(0,1,(3,)))

    	positions = np.random.uniform(-1,1,(10, 3)).astype(np.float32)
    	imdraw.lines(prog, positions)
    	time.sleep(1/8)

    glfw.swap_buffers(window)
    glfw.poll_events()
glfw.terminate()
