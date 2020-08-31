from OpenGL.GL import *
import numpy as np
from .helpers import buffer_offset
from editor.render.puregl import program
from editor.render import glsl

from . import quad

def texture(tex, rect=None):
	debug_quad_program = program.create(*glsl.read('debug_quad.vs', 'debug_quad_depth.fs'))


	if rect is None:
		rect = (0,0,window.width, window.height)
	glViewport(*rect)
	glUseProgram(debug_quad_program)

	program.set_uniform(debug_quad_program, 'projectionMatrix', np.eye(4))
	program.set_uniform(debug_quad_program, 'viewMatrix', np.eye(4))
	program.set_uniform(debug_quad_program, 'modelMatrix', np.eye(4))
	program.set_uniform(debug_quad_program, 'tex', 0)
	glActiveTexture(GL_TEXTURE0+0)
	glBindTexture(GL_TEXTURE_2D, tex)
	quad(debug_quad_program)
	glBindTexture(GL_TEXTURE_2D, 0)
	glUseProgram(0)