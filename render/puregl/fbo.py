from contextlib import contextmanager
from OpenGL.GL import *
import numpy as np


@contextmanager
def bind(framebuffer, write=None):
	if write is None:
		glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
		yield framebuffer
		glBindFramebuffer(GL_FRAMEBUFFER, 0)
	else:
		glBindFramebuffer(GL_READ_FRAMEBUFFER, framebuffer)
		glBindFramebuffer(GL_DRAW_FRAMEBUFFER, write)
		yield framebuffer, write
		glBindFramebuffer(GL_READ_FRAMEBUFFER, 0)
		glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)


STATUS = {
	GL_FRAMEBUFFER_COMPLETE: 'GL_FRAMEBUFFER_COMPLETE',
	GL_FRAMEBUFFER_UNDEFINED: 'GL_FRAMEBUFFER_UNDEFINED',
	GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT: 'GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT',
	GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT: 'GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT',
	GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER: 'GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER',
	GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER: 'GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER',
	GL_FRAMEBUFFER_UNSUPPORTED: 'GL_FRAMEBUFFER_UNSUPPORTED'
}
