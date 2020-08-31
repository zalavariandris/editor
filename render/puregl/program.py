from OpenGL.GL import *
from contextlib import contextmanager
from editor.utils import memoize

import logging

@memoize
def create(vs, fs):
	logging.debug('create program')
	# create certex shader
	vertex_shader = glCreateShader(GL_VERTEX_SHADER)
	glShaderSource(vertex_shader, vs)
	glCompileShader(vertex_shader)
	if glGetShaderiv(vertex_shader, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(vertex_shader))

	#create fragment shader
	fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
	glShaderSource(fragment_shader, fs)
	glCompileShader(fragment_shader)
	if glGetShaderiv(fragment_shader, GL_INFO_LOG_LENGTH): # compilation error check
		raise Exception(glGetShaderInfoLog(fragment_shader))

	# link shaders
	program = glCreateProgram()
	glAttachShader(program, vertex_shader)
	glAttachShader(program, fragment_shader)
	glLinkProgram(program)
	if glGetProgramiv(program, GL_INFO_LOG_LENGTH): # link error check
		raise Exception(glGetProgramInfoLog(program))

	return program

def set_uniform(program, name, value):
	import glm
	import numpy as np
	location = glGetUniformLocation(program, name)

	if isinstance(value, np.ndarray):
		if value.shape == (4, 4): # matrix
			glUniformMatrix4fv(location, 1, False, value)
		elif value.shape == (3,):
			glUniform3f(location, value[0], value[1], value[2])
		else:
			raise NotImplementedError('uniform {} {}'.format(type(value), value.shape))

	elif isinstance(value, glm.mat4):
		glUniformMatrix4fv(location, 1, False, np.array(value))
	elif isinstance(value, glm.mat3):
		glUniformMatrix3fv(location, 1, False, np.array(value))
	elif isinstance(value, glm.vec3):
		glUniform3f(location, value.x, value.y, value.z)

	elif isinstance(value, tuple):
		if len(value)==3:
			glUniform3f(location, value[0], value[1], value[2])

	elif isinstance(value, bool):
			glUniform1i(location, value)
	elif isinstance(value, int):
			glUniform1i(location, value)
	elif isinstance(value, float):
			glUniform1f(location, value)
	else:
		raise NotImplementedError(type(value))


@contextmanager
def use(prog):
	glUseProgram(prog) #FIXME: push pip current program
	yield prog
	glUseProgram(0)