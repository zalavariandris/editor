from editor.render import gloo
from editor.utils import profile
from editor.render.gloo.helpers import box, plane, buffer_offset
from editor.render.window import GLFWViewer
from OpenGL.GL import *

import numpy as np
from pathlib import Path
import glm
import math

vertexShader = """
#version 330 core
in vec3 position;
in vec2 uv;

uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;



out vec2 vUv;

void main(){
	gl_PointSize = 5.0;
	vUv = uv;
	gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1);
}
"""

fragmentShader = """
#version 330 core
in vec2 vUv;
out vec4 color;
uniform sampler2D diffuseMap;

void main(){
	vec3 tex = texture(diffuseMap, vUv).rgb;
	color = vec4(tex, 1.0);
}
"""


# Init
width, height = 640, 480
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

# create geometry
Vertex = np.dtype([('position', np.float32, 3),
				   ('uv', np.float32, 2)])
geo = box()

vertices = np.zeros(6*4, Vertex)
vertices['position'] = geo['positions']
vertices['uv'] = geo['uvs']

# Setup opengl context
with window:
	glEnable(GL_PROGRAM_POINT_SIZE)
	glEnable(GL_DEPTH_TEST)

	program = gloo.Program(vertexShader, fragmentShader)
	noise_data = np.random.uniform( 0,1, (64,64,3)).astype(np.float32)
	texture = gloo.Texture.from_data(noise_data, slot=0)
	
	# upload geomery to GPU
	indexBuffer = gloo.EBO(geo['indices'])
	vao = gloo.VAO()



	with program, vao:
		# single VBO from structured ndarray to VAO
		offset = 0
		vbo = gloo.VBO(vertices)
		gtypes={
			np.float32: GL_FLOAT
		}
		for name in vertices.dtype.names:
			location = program.get_attribute_location(name)
			size = vertices[name].shape[1]
			gtype = gtypes[np.float32]
			stride = vertices.itemsize
			vao.enable_vertex_attribute(location)
			vao.add_vertex_attribute(location, vbo, size, GL_FLOAT, stride=stride, offset=offset)
			offset+=vertices.dtype[name].itemsize


# Draw
with window:
	while not window.should_close():
		with program:
			glViewport(0, 0, window.width, window.height)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

			program.set_uniform('projectionMatrix', window.projection_matrix)
			program.set_uniform('viewMatrix', window.view_matrix)
			program.set_uniform('modelMatrix', model_matrix)

			program.set_uniform('diffuseMap', texture.texture_unit)

			with vao, indexBuffer, texture:
				count = indexBuffer.count
				glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)
				glDrawElements(GL_POINTS, count, GL_UNSIGNED_INT, None)

			window.swap_buffers()
			GLFWViewer.poll_events()