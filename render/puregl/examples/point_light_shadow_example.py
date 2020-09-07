from OpenGL.GL import *
import numpy as np
import glm

from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program
from editor.render import glsl


width, height = 1024, 768
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

with window:
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_CULL_FACE)

	lambert_program = program.create(
		"""
		#version 330 core
		uniform mat4 projectionMatrix;
		uniform mat4 viewMatrix;
		uniform mat4 modelMatrix;

		layout (location = 0) in vec3 position;
		layout (location = 2) in vec3 normal;

		out vec3 Normal;
		out vec3 FragPos;

		void main(){
			Normal = normal;
			FragPos = (modelMatrix * vec4(position, 1.0)).xyz;
			gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1.0);
		}
		""",

		"""
		#version 330 core

		in vec3 FragPos;
		in vec3 Normal;
		uniform vec3 lightPos;
		out vec4 FragColor;
		void main(){
			vec3 N = normalize(Normal);
			vec3 L = normalize(lightPos-FragPos);
			float luminance = max(dot(L, N), 0.0);
			vec3 color = vec3(luminance);
			FragColor = vec4(color,1);
		}
		"""
	)

with window:
	while not window.should_close():
		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		with program.use(lambert_program) as prog:
			program.set_uniform(prog, 'projectionMatrix', window.projection_matrix)
			program.set_uniform(prog, 'viewMatrix', window.view_matrix)
			program.set_uniform(prog, 'lightPos', (-2,3,3))


			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (0,0.5, 0)))
			imdraw.cube(prog)

			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (0,0.0, 0)))
			imdraw.plane(prog)

			# draw grid

		window.swap_buffers()
		GLFWViewer.poll_events()