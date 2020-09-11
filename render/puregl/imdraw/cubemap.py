from OpenGL.GL import *
import numpy as np
import glm

from . import cube
from .. import program


def cubemap(tex, rect, projection, view):
	prog = program.create(
		"""
		#version 330 core
		layout (location=0) in vec3 position;
		uniform mat4 projectionMatrix;
		uniform mat4 viewMatrix;
		uniform mat4 modelMatrix;
		out vec3 FragPos;
		void main(){
			FragPos = (modelMatrix * vec4(position, 1.0)).xyz;
			gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1.0);
		}

		""",
		"""
		#version 330 core
		out vec4 FragColor;
		in vec3 FragPos;
		uniform samplerCube cubeMap;
		void main(){
			vec3 normal = normalize(FragPos);
			vec3 color = texture(cubeMap, normal).rgb;
			FragColor = vec4(color, 1.0);
		}
		""")

	glViewport(*rect)
	with program.use(prog):
		glActiveTexture(GL_TEXTURE0+0)
		glBindTexture(GL_TEXTURE_CUBE_MAP, tex)
		program.set_uniform(prog, "projectionMatrix", projection)
		program.set_uniform(prog, "viewMatrix", view)
		program.set_uniform(prog, "modelMatrix", glm.scale(glm.mat4(1), (1.1, 1.1, 1.1)))
		program.set_uniform(prog, "cubeMap", 0)
		cube(prog)
		glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
