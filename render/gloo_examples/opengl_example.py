from editor.render import gloo
from editor.utils import profile
from editor.render.gloo.helpers import box, plane
from editor.render.window import GLFWViewer
from OpenGL.GL import *

import numpy as np
from pathlib import Path
import glm
import math
from PIL import Image

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
geo_data = box()
diffuse_data = np.array(Image.open('../assets/container2.png'), dtype=np.float32)[:,:,:3]/255
specular_data = np.array(Image.open('../assets/container2_specular.png'), dtype=np.float32)[:,:,:3]/255

with window:
	glEnable(GL_PROGRAM_POINT_SIZE)
	glEnable(GL_DEPTH_TEST)

	# create geometry
	elements_id, positions_id, uv_id = glGenBuffers(3)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, elements_id)
	glBufferData(GL_ELEMENT_ARRAY_BUFFER, geo_data['indices'].nbytes, geo_data['indices'], GL_STATIC_DRAW)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

	glBindBuffer(GL_ARRAY_BUFFER, positions_id)
	glBufferData(GL_ARRAY_BUFFER, geo_data['positions'].nbytes, geo_data['positions'], GL_STATIC_DRAW)
	glBindBuffer(GL_ARRAY_BUFFER, 0)

	glBindBuffer(GL_ARRAY_BUFFER, uv_id)
	glBufferData(GL_ARRAY_BUFFER, geo_data['uvs'].nbytes, geo_data['uvs'], GL_STATIC_DRAW)
	glBindBuffer(GL_ARRAY_BUFFER, 0)

	# create textures
	diffuse_tex, specular_tex = glGenTextures(2)
	glActiveTexture(GL_TEXTURE0+0)
	glBindTexture(GL_TEXTURE_2D, diffuse_tex)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, diffuse_data.shape[1], diffuse_data.shape[0], 0, GL_BGR, GL_FLOAT, diffuse_data)

	glActiveTexture(GL_TEXTURE0+1)
	glBindTexture(GL_TEXTURE_2D, specular_tex)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, specular_data.shape[1], specular_data.shape[0], 0, GL_BGR, GL_FLOAT, specular_data)

	glBindTexture(GL_TEXTURE_2D, 0)
	
	# create program
	vshader_id = glCreateShader(GL_VERTEX_SHADER)
	glShaderSource(vshader_id, vertexShader)
	glCompileShader(vshader_id)
	if glGetShaderiv(vshader_id, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(shader_id))

	fshader_id = glCreateShader(GL_FRAGMENT_SHADER)
	glShaderSource(fshader_id,fragmentShader)
	glCompileShader(fshader_id)
	if glGetShaderiv(vshader_id, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(shader_id))

	program_id = glCreateProgram()
	glAttachShader(program_id, vshader_id)
	glAttachShader(program_id, fshader_id)
	glLinkProgram(program_id)
	if glGetProgramiv(program_id, GL_INFO_LOG_LENGTH): # link error check
		raise Exception(glGetProgramInfoLog(shader_id))

	# set program attributes
	vao = glGenVertexArrays(1)
	glBindVertexArray(vao)
	glBindBuffer(GL_ARRAY_BUFFER, positions_id)
	location = glGetAttribLocation(program_id, 'position')
	glEnableVertexAttribArray(location)
	glVertexAttribPointer(location, 3, GL_FLOAT, False, 0, None)

	glBindBuffer(GL_ARRAY_BUFFER, uv_id)
	location = glGetAttribLocation(program_id, 'uv')
	glEnableVertexAttribArray(location)
	glVertexAttribPointer(location, 2, GL_FLOAT, False, 0, None)
	
	glBindVertexArray(0)

# Draw
with window:
	while not window.should_close():
		# clear window
		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		# set program uniforms
		glUseProgram(program_id)
		location = glGetUniformLocation(program_id, 'projectionMatrix')
		glUniformMatrix4fv(location, 1, False, np.array(window.projection_matrix))
		location = glGetUniformLocation(program_id, 'viewMatrix')
		glUniformMatrix4fv(location, 1, False, np.array(window.view_matrix))
		location = glGetUniformLocation(program_id, 'modelMatrix')
		glUniformMatrix4fv(location, 1, False, np.eye(4))
		
		# draw geometry
		glBindVertexArray(vao)
		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, elements_id)
		glDrawElements(GL_TRIANGLES, geo_data['indices'].size, GL_UNSIGNED_INT, None)
		glDrawElements(GL_POINTS, geo_data['indices'].size, GL_UNSIGNED_INT, None)
		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

		# swap buffers
		window.swap_buffers()
		GLFWViewer.poll_events()