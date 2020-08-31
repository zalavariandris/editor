from contextlib import contextmanager
from OpenGL.GL import *

@contextmanager
def bind(framebuffer):
	glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
	yield framebuffer
	glBindFramebuffer(GL_FRAMEBUFFER, 0)