from OpenGL.GL import *
from contextlib import contextmanager
import numpy as np
from .helpers import buffer_offset
from editor.render.puregl import program
from editor.render import glsl

from . import quad


def texture(tex, rect, shuffle=(0, 1, 2, -1)):
	# create shader program
	debug_quad_program = program.create(*glsl.read('debug_quad.vs', 'shuffle.fs'))

	# setup program uniforms
	with program.use(debug_quad_program):
		program.set_uniform(debug_quad_program, 'projectionMatrix', np.eye(4))
		program.set_uniform(debug_quad_program, 'viewMatrix', np.eye(4))
		program.set_uniform(debug_quad_program, 'modelMatrix', np.eye(4))
		program.set_uniform(debug_quad_program, 'tex', 0)
		program.set_uniform(debug_quad_program, 'shuffle.red',   shuffle[0])
		program.set_uniform(debug_quad_program, 'shuffle.green', shuffle[1])
		program.set_uniform(debug_quad_program, 'shuffle.blue',  shuffle[2])
		program.set_uniform(debug_quad_program, 'shuffle.alpha', shuffle[3])

	glViewport(*rect)

	# draw texture quad
	with program.use(debug_quad_program):
		glActiveTexture(GL_TEXTURE0+0)
		glBindTexture(GL_TEXTURE_2D, tex)
		quad(debug_quad_program)
		glBindTexture(GL_TEXTURE_2D, 0)


@contextmanager
def bind(target, tex):
	glBindTexture(target, tex)
	yield tex
	glBindTexture(target, 0)
