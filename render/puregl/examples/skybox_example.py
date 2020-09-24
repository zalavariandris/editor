from OpenGL.GL import *
from editor.render.window import GLFWViewer
import numpy as np
from editor.render.puregl import program

from editor.render import glsl, imdraw
import glm
import logging
logging.basicConfig(filename=None, level=logging.DEBUG, format='%(levelname)s:%(module)s.%(funcName)s: %(message)s')


width, height = 1024, 768
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

with window:
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_CULL_FACE)

	

	while not window.should_close():
		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		with program.use(skybox_program):
			program.set_uniform(skybox_program, 'projection', window.projection_matrix)
			sky_view = glm.mat4(glm.mat3(window.view_matrix)); 
			program.set_uniform(skybox_program, 'view', sky_view)
			camera_pos = glm.transpose(glm.transpose(glm.inverse(window.view_matrix)))[3].xyz
			program.set_uniform(skybox_program, 'cameraPos', camera_pos)
			program.set_uniform(skybox_program, 'skybox', 0)
			program.set_uniform(skybox_program, 'groundProjection', True)
			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_CUBE_MAP, env_cubemap)
			imdraw.cube(skybox_program, flip=True)
			
			glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
		glDepthMask(GL_TRUE)

			# draw grid

		window.swap_buffers()
		GLFWViewer.poll_events()