from OpenGL.GL import *
import numpy as np
import glm
import sys;
import glfw

from pathlib import Path




class Shader:
		def __init__(self, vertex, fragment, geometry=None):
			shaders = {
				GL_VERTEX_SHADER: vertex,
				GL_FRAGMENT_SHADER: fragment
			}
				
			# FIXME: check for a valid contex
			# and throw an error before using gl commands
			self.program_id = glCreateProgram()

			try:
				self.shader_ids = []
				for shader_type, shader_src in shaders.items():
					shader_id = glCreateShader(shader_type)
					glShaderSource(shader_id, shader_src)

					glCompileShader(shader_id)

					# check if compilation was successful
					result = glGetShaderiv(shader_id, GL_COMPILE_STATUS)
					info_log_len = glGetShaderiv(shader_id, GL_INFO_LOG_LENGTH)
					if info_log_len:
						logmsg = glGetShaderInfoLog(shader_id)
						print(logmsg)
						sys.exit(10)

					glAttachShader(self.program_id, shader_id)
					self.shader_ids.append(shader_id)

				glLinkProgram(self.program_id)

				# check if linking was successful
				result = glGetProgramiv(self.program_id, GL_LINK_STATUS)
				info_log_len = glGetProgramiv(self.program_id, GL_INFO_LOG_LENGTH)
				if info_log_len:
					logmsg = glGetProgramInfoLog(self.program_id)
					print(logmsg)
					sys.exit(11)

					
			except Exception as err:
				raise err

		def __enter__(self):
				glUseProgram(self.program_id)
				return self

		def __exit__(self, type, value, traceback):
				glUseProgram(0)

		def __del__(self):
				for shader_id in self.shader_ids:
						glDetachShader(self.program_id, shader_id)
						glDeleteShader(shader_id)
				glDeleteProgram(self.program_id)
				print("delete shader program")

		def get_uniform_location(self, name):
				location = glGetUniformLocation(self.program_id, name)
				assert location>=0
				return location

		def set_uniform(self, name, value: [np.ndarray, int, glm.mat4x4]):
				location = self.get_uniform_location(name)

				if isinstance(value, np.ndarray):
						if value.shape == (4, 4): # matrix
								glUniformMatrix4fv(location, 1, False, value)
						elif value.shape == (3,):
								glUniform3f(location, value[0], value[1], value[2])
						else:
								raise NotImplementedError('uniform {} {}'.format(type(value), value.shape))
				
				elif isinstance(value, glm.mat4x4):
						glUniformMatrix4fv(location, 1, False, np.array(value))
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

		def get_attribute_location(self, attribute_name):
				assert self.program_id == glGetIntegerv(GL_CURRENT_PROGRAM)
				return glGetAttribLocation(self.program_id, attribute_name)
