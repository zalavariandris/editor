from OpenGL.GL import *
from editor.render.window import GLFWViewer
import numpy as np
from editor.render.puregl import imdraw, program

from editor.render import glsl
width, height = 1024, 768
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

with window:
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_CULL_FACE)

	prog = program.create(
		"""
		#version 330 core
		uniform mat4 projectionMatrix;
		uniform mat4 viewMatrix;
		uniform mat4 modelMatrix;

		layout (location = 0) in vec3 position;

		void main(){
			gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1.0);
		}
		""", 
		"""
		#version 330 core
		out vec4 FragColor;
		void main(){
			FragColor = vec4(1,1,1,1);
		}
		"""
	)

	while not window.should_close():
		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		with program.use(prog):
			program.set_uniform(prog, 'projectionMatrix', window.projection_matrix)
			program.set_uniform(prog, 'viewMatrix', window.view_matrix)
			program.set_uniform(prog, 'modelMatrix', np.eye(4))
			imdraw.cube(prog)

			# draw grid

		window.swap_buffers()
		GLFWViewer.poll_events()