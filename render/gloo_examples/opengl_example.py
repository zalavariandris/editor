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
from editor import utils


from editor.render.gloo.helpers import buffer_offset
from editor.utils import memoize

def drawQuad():
	@memoize
	def vao(cache):
		print('create vao', cache)
		quadVertices = np.array(
			# positions        # texture Coords
			[-1.0,  1.0, 0.0, 0.0, 1.0,
			-1.0, -1.0, 0.0, 0.0, 0.0,
			 1.0,  1.0, 0.0, 1.0, 1.0,
			 1.0, -1.0, 0.0, 1.0, 0.0,],
			dtype=np.float32
		)

		# setup plane VAO
		quadVAO = glGenVertexArrays(1)
		quadVBO = glGenBuffers(1)
		glBindVertexArray(quadVAO)
		glBindBuffer(GL_ARRAY_BUFFER, quadVBO)
		glBufferData(GL_ARRAY_BUFFER, quadVertices.nbytes, quadVertices, GL_STATIC_DRAW)
		glEnableVertexAttribArray(0)
		glVertexAttribPointer(0, 3, GL_FLOAT, False, 5*quadVertices.itemsize, buffer_offset(0))
		glEnableVertexAttribArray(1);
		glVertexAttribPointer(1, 2, GL_FLOAT, False, 5*quadVertices.itemsize, buffer_offset(3))

		return quadVAO

	glBindVertexArray(vao(10))
	glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
	glBindVertexArray(0)

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

depth_vertex_shader = """
#version 330 core

in vec3 position;
uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;
uniform mat4 modelMatrix;

void main()
{
	gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1.0);
}
"""

depth_fragment_shader = """
#version 330 core

void main(){
	// gl_FragDepth = gl_FragCoord.z;
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
		raise Exception(glGetShaderInfoLog(vshader_id))

	fshader_id = glCreateShader(GL_FRAGMENT_SHADER)
	glShaderSource(fshader_id,fragmentShader)
	glCompileShader(fshader_id)
	if glGetShaderiv(fshader_id, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(fshader_id))

	program_id = glCreateProgram()
	glAttachShader(program_id, vshader_id)
	glAttachShader(program_id, fshader_id)
	glLinkProgram(program_id)
	if glGetProgramiv(program_id, GL_INFO_LOG_LENGTH): # link error check
		raise Exception(glGetProgramInfoLog(program_id))

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

	# create lights
	depthfbo = glGenFramebuffers(1)
	shadow_width, shadow_height = 1024,1024
	depthmap = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, depthmap)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, shadow_width, shadow_height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

	# attach depthmap to framebuffer
	glBindFramebuffer(GL_FRAMEBUFFER, depthfbo)
	glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, depthmap, 0)
	glDrawBuffer(GL_NONE) # dont render color data
	glReadBuffer(GL_NONE)
	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	# create depth program
	vshader_id = glCreateShader(GL_VERTEX_SHADER)
	glShaderSource(vshader_id, depth_vertex_shader)
	glCompileShader(vshader_id)
	if glGetShaderiv(vshader_id, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(vshader_id))

	fshader_id = glCreateShader(GL_FRAGMENT_SHADER)
	glShaderSource(fshader_id, depth_fragment_shader)
	glCompileShader(fshader_id)
	if glGetShaderiv(fshader_id, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(fshader_id))

	depth_program = glCreateProgram()
	glAttachShader(depth_program, vshader_id)
	glAttachShader(depth_program, fshader_id)
	glLinkProgram(depth_program)
	if glGetProgramiv(depth_program, GL_INFO_LOG_LENGTH): # link error check
		raise Exception(glGetProgramInfoLog(depth_program))

# Draw
with window:
	while not window.should_close():
		# 1. render scene to depth map
		# configure shader
		light_projection = glm.ortho(-10,10,-10,10, 0.1,100)
		light_view = glm.lookAt((-2,4,-1), (0,0,0), (0,1,0))

		glUseProgram(depth_program)
		location = glGetUniformLocation(depth_program, 'projectionMatrix')
		glUniformMatrix4fv(location, 1, False, np.array(light_projection))
		location = glGetUniformLocation(depth_program, 'viewMatrix')
		glUniformMatrix4fv(location, 1, False, np.array(light_view))
		location = glGetUniformLocation(depth_program, 'modelMatrix')
		glUniformMatrix4fv(location, 1, False, np.eye(4))
		
		glViewport(0,0,shadow_width, shadow_height)
		glBindFramebuffer(GL_FRAMEBUFFER, depthfbo)
		glClear(GL_DEPTH_BUFFER_BIT)
		# draw geometry
		glBindVertexArray(vao)
		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, elements_id)
		glDrawElements(GL_TRIANGLES, geo_data['indices'].size, GL_UNSIGNED_INT, None)
		glDrawElements(GL_POINTS, geo_data['indices'].size, GL_UNSIGNED_INT, None)
		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
		glBindFramebuffer(GL_FRAMEBUFFER, 0)

		# 2. render the scene as normal with shdow mapping
		# clear window
		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		
		# configure shader
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

		# draw quad
		drawQuad()

		# swap buffers
		window.swap_buffers()
		GLFWViewer.poll_events()