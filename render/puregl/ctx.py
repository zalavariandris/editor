from contextlib import contextmanager
from OpenGL.GL import *

@contextmanager
def fbo(framebuffer):
	glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
	yield framebuffer
	glBindFramebuffer(GL_FRAMEBUFFER, 0)


@contextmanager
def program(prog):
	glUseProgram(prog)
	yield prog
	glUseProgram(0)