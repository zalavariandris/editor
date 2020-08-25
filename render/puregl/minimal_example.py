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
from draw import draw_quad, draw_cube

vertex_source = """
#version 330 core
layout (location = 0) in vec3 position;
layout (location = 1) in vec2 uv;
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

fragment_source = """
#version 330 core
in vec2 vUv;
uniform sampler2D diffuseMap;
out vec4 color;

void main(){
	vec3 tex = texture(diffuseMap, vUv).rgb;
	color = vec4(tex, 1.0);
}
"""

depth_vertex_source = """
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

depth_fragment_source = """
#version 330 core

void main(){
	// gl_FragDepth = gl_FragCoord.z;
}
"""

depth_to_color_fragment_source = """
#version 330 core
in vec2 vUv;
uniform sampler2D depthMap;
out vec4 color;

void main(){
	float depthValue = texture(depthMap, vUv).r;
	color = vec4(vec3(depthValue), 1.0);
}
"""

def use_program(vertex_source, fragment_source):
	try:
		try:
			memo = use_program.memo
		except AttributeError:
			use_program.memo = dict()
			memo = use_program.memo
		program = memo[(vertex_source, fragment_source)]
	except KeyError:
		print('create program')
		# setup
		vertex_shader = glCreateShader(GL_VERTEX_SHADER)
		glShaderSource(vertex_shader, vertex_source)
		glCompileShader(vertex_shader)
		if glGetShaderiv(vertex_shader, GL_INFO_LOG_LENGTH): # compilation error check
			raise Exception(glGetShaderInfoLog(vertex_shader))

		fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
		glShaderSource(fragment_shader, depth_to_color_fragment_source)
		glCompileShader(fragment_shader)
		if glGetShaderiv(fragment_shader, GL_INFO_LOG_LENGTH): # compilation error check
			raise Exception(glGetShaderInfoLog(fragment_shader))

		program = glCreateProgram()
		glAttachShader(program, vertex_shader)
		glAttachShader(program, fragment_shader)
		glLinkProgram(program)
		if glGetProgramiv(program, GL_INFO_LOG_LENGTH): # link error check
			raise Exception(glGetProgramInfoLog(program))

		use_program.memo[(vertex_source, fragment_source)]=program

	# draw
	glUseProgram(program)
	return program
	
from multipledispatch import dispatch

def texture_with_data(data, slot, format):
	# get/create memo attribute
	try:
		memo = texture_with_data.memo
	except AttributeError:
		print("-setup memo")
		memo = dict()
		texture_with_data.memo = memo

	# get, create texture
	try:
		tex = memo[(id(data), slot)]
	except KeyError:
		print("-generate texture")
		tex = glGenTextures(1)
		glActiveTexture(GL_TEXTURE0+slot)
		glBindTexture(GL_TEXTURE_2D, tex)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		internalformat = {
			GL_RGB: GL_RGB,
			GL_BGR: GL_RGB,
			GL_DEPTH_COMPONENT: GL_DEPTH_COMPONENT
		}[format]
		#FIXME: read internal and formats https://www.khronos.org/registry/OpenGL-Refpages/gl4/html/glTexImage2D.xhtml
		glTexImage2D(GL_TEXTURE_2D, 0, internalformat, data.shape[1], data.shape[0], 0, format, GL_FLOAT, data)
		
		memo[(id(data), slot)] = tex

	return tex


def texture_with_size(width, height, slot, format):
	# get/create memo attribute
	try:
		memo = texture_with_data.memo
	except AttributeError:
		print("-setup memo")
		memo = dict()
		texture_with_data.memo = memo

	# get, create texture
	try:
		tex = memo[(width, height, slot)]
	except KeyError:
		print("-generate texture")
		tex = glGenTextures(1)
		glActiveTexture(GL_TEXTURE0+slot)
		glBindTexture(GL_TEXTURE_2D, tex)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexImage2D(GL_TEXTURE_2D, 0, format, width, height, 0, format, GL_FLOAT, None)
		
		memo[(width, height, slot)] = tex

	return tex

# Init
width, height = 640, 480
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

# create geometry
diffuse_data = np.array(Image.open('../assets/container2.png'))[...,[2,1,0]]/255
specular_data = np.array(Image.open('../assets/container2_specular.png'))[...,[2,1,0]]/255

with window:
	glEnable(GL_PROGRAM_POINT_SIZE)
	glEnable(GL_DEPTH_TEST)

	texture_with_data(diffuse_data, slot=0, format=GL_BGR)
	texture_with_data(specular_data, slot=1, format=GL_BGR)
	depth_tex = texture_with_size(1024,1024, slot=2, format=GL_DEPTH_COMPONENT)
	
	# create program
	vertex_shader = glCreateShader(GL_VERTEX_SHADER)
	glShaderSource(vertex_shader, vertex_source)
	glCompileShader(vertex_shader)
	if glGetShaderiv(vertex_shader, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(vertex_shader))

	fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
	glShaderSource(fragment_shader,fragment_source)
	glCompileShader(fragment_shader)
	if glGetShaderiv(fragment_shader, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(fragment_shader))

	program = glCreateProgram()
	glAttachShader(program, vertex_shader)
	glAttachShader(program, fragment_shader)
	glLinkProgram(program)
	if glGetProgramiv(program, GL_INFO_LOG_LENGTH): # link error check
		raise Exception(glGetProgramInfoLog(program))

	# create lights
	depthfbo = glGenFramebuffers(1)
	

	# attach depthmap to framebuffer
	glBindFramebuffer(GL_FRAMEBUFFER, depthfbo)
	glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, depth_tex, 0)
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
	glDrawBuffer(GL_NONE) # dont render color data
	glReadBuffer(GL_NONE)
	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	# create depth program
	vertex_shader = glCreateShader(GL_VERTEX_SHADER)
	glShaderSource(vertex_shader, depth_vertex_source)
	glCompileShader(vertex_shader)
	if glGetShaderiv(vertex_shader, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(vertex_shader))

	fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
	glShaderSource(fragment_shader, depth_fragment_source)
	glCompileShader(fragment_shader)
	if glGetShaderiv(fragment_shader, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(fragment_shader))

	depth_program = glCreateProgram()
	glAttachShader(depth_program, vertex_shader)
	glAttachShader(depth_program, fragment_shader)
	glLinkProgram(depth_program)
	if glGetProgramiv(depth_program, GL_INFO_LOG_LENGTH): # link error check
		raise Exception(glGetProgramInfoLog(depth_program))


	# create display depth component program
	vertex_shader = glCreateShader(GL_VERTEX_SHADER)
	glShaderSource(vertex_shader, vertex_source)
	glCompileShader(vertex_shader)
	if glGetShaderiv(vertex_shader, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(vertex_shader))

	fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
	glShaderSource(fragment_shader, depth_to_color_fragment_source)
	glCompileShader(fragment_shader)
	if glGetShaderiv(fragment_shader, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(fragment_shader))

	fbo_depth_on_screen = glCreateProgram()
	glAttachShader(fbo_depth_on_screen, vertex_shader)
	glAttachShader(fbo_depth_on_screen, fragment_shader)
	glLinkProgram(fbo_depth_on_screen)
	if glGetProgramiv(fbo_depth_on_screen, GL_INFO_LOG_LENGTH): # link error check
		raise Exception(glGetProgramInfoLog(fbo_depth_on_screen))


# Draw
with window:
	while not window.should_close():
		# 1. render scene to depth map
		glBindFramebuffer(GL_FRAMEBUFFER, depthfbo)
		
		glViewport(0,0,1024, 1024)
		glClear(GL_DEPTH_BUFFER_BIT)

		# configure shader
		light_projection = glm.ortho(-2,2,-2,2, 0.5,3)
		light_view = glm.lookAt((-1,1,-1), (0,0,0), (0,1,0))

		glUseProgram(depth_program)
		glUniformMatrix4fv(glGetUniformLocation(depth_program, 'projectionMatrix'), 1, False, np.array(light_projection))
		glUniformMatrix4fv(glGetUniformLocation(depth_program, 'viewMatrix'), 1, False, np.array(light_view))
		glUniformMatrix4fv(glGetUniformLocation(depth_program, 'modelMatrix'), 1, False, np.eye(4))
		
		# draw geometry
		
		draw_cube(program)
		draw_quad(program)
		
		glBindFramebuffer(GL_FRAMEBUFFER, 0)

		# 2. render the scene as normal with shdow mapping
		# clear window
		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		


		# # configure shader
		# glUseProgram(program)
		# glUniformMatrix4fv(glGetUniformLocation(program, 'projectionMatrix'), 1, False, np.array(window.projection_matrix))
		# glUniformMatrix4fv(glGetUniformLocation(program, 'viewMatrix'), 1, False, np.array(window.view_matrix))
		# glUniformMatrix4fv(glGetUniformLocation(program, 'modelMatrix'), 1, False, np.eye(4))
		# glUniform1i(glGetUniformLocation(program, 'diffuseMap'), 0)
		
		# # draw geometry

		# draw_cube(program)
		# draw_quad(program)

		# render fbo depth component on quad
		glUseProgram(fbo_depth_on_screen)
		fbo_depth_on_screen = use_program(vertex_source, depth_to_color_fragment_source)

		glUniformMatrix4fv(glGetUniformLocation(fbo_depth_on_screen, 'projectionMatrix'), 1, False, np.array(window.projection_matrix))
		glUniformMatrix4fv(glGetUniformLocation(fbo_depth_on_screen, 'viewMatrix'), 1, False, np.array(window.view_matrix))
		glUniformMatrix4fv(glGetUniformLocation(fbo_depth_on_screen, 'modelMatrix'), 1, False, np.eye(4))
		glUniform1i(glGetUniformLocation(fbo_depth_on_screen, 'depthMap'), 2)
		draw_quad(fbo_depth_on_screen)

		# swap buffers
		window.swap_buffers()
		GLFWViewer.poll_events()