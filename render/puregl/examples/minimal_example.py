from OpenGL.GL import *
from editor.render.window import GLFWViewer
import numpy as np
from editor.render.puregl import imdraw, program

from editor.render import glsl

import logging
logging.basicConfig(filename=None, level=logging.DEBUG, format='%(levelname)s:%(module)s.%(funcName)s: %(message)s')


width, height = 1024, 768
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

with window:
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_CULL_FACE)

	prog = program.create(
		"""
		#version 330 core
		uniform mat4 projection;
		uniform mat4 view;
		uniform mat4 model;

		layout (location = 0) in vec3 position;

		void main(){
			gl_Position = projection * view * model * vec4(position, 1.0);
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
			program.set_uniform(prog, 'projection', window.projection_matrix)
			program.set_uniform(prog, 'view', window.view_matrix)
			program.set_uniform(prog, 'model', np.eye(4))
			imdraw.cube(prog)

			# draw grid

		window.swap_buffers()
		GLFWViewer.poll_events()