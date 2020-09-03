from OpenGL.GL import *
import numpy as np
import glm

from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program, fbo
from editor.render import glsl


width, height = 1024, 768
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

with window:
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_CULL_FACE)


	# Geometry Pass
	# =============
	gBuffer = glGenFramebuffers(1)
	geometry_program = program.create(*glsl.read("deferred_geometry"))
	colorBuffer, positionBuffer, normalBuffer = glGenTextures(3)

	glBindFramebuffer(GL_FRAMEBUFFER, gBuffer)
	glDrawBuffers(3, [GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1, GL_COLOR_ATTACHMENT2])
	for i, buffer in enumerate([colorBuffer, positionBuffer, normalBuffer]):
		glBindTexture(GL_TEXTURE_2D, buffer)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, width, height, 0, GL_RGB, GL_FLOAT, None)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glFramebufferTexture2D(
			GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0+i, GL_TEXTURE_2D, buffer, 0
		)
		glBindTexture(GL_TEXTURE_2D, 0)

	# create depth+stencil buffer
	rbo = glGenRenderbuffers(1)
	glBindRenderbuffer(GL_RENDERBUFFER, rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
	glBindRenderbuffer(GL_RENDERBUFFER, 0)

	glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	# Lightin pass
	# ============

with window:
	while not window.should_close():
		glViewport(0,0,window.width,window.height);
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		# imdraw.texture(colorBuffer, (0,0,window.width, window.height))

		window.swap_buffers()
		GLFWViewer.poll_events()