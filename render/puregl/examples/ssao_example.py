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

	ssao_geometry_program = program.create(*glsl.read("ssao_geometry"))

	# create gBuffer
	# --------------
	gBuffer = glGenFramebuffers(1)
	ssao_width = window.width
	ssao_height = window.height
	gPosition, gNormal, gAlbedo = glGenTextures(3)

	with fbo.bind(gBuffer):
		# create color attachments
		glDrawBuffers(3, [GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1, GL_COLOR_ATTACHMENT2])
		for i, tex in enumerate([gPosition, gNormal, gAlbedo]):
			glBindTexture(GL_TEXTURE_2D, tex)
			glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, ssao_width, ssao_height, 0, GL_RGB, GL_FLOAT, None)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		
			# attach to color
			glFramebufferTexture2D(
				GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0 + i, GL_TEXTURE_2D, tex, 0
			)
			glBindTexture(GL_TEXTURE_2D, 0)

		# create depth+stencil buffer
		rbo = glGenRenderbuffers(1)
		glBindRenderbuffer(GL_RENDERBUFFER, rbo)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, ssao_width, ssao_height)
		glBindRenderbuffer(GL_RENDERBUFFER, 0)

		glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
		assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	ssao_program = program.create(*glsl.read("ssao"))
	ssao_blur_program = program.create(*glsl.read('ssao.vs', "ssao_blur.fs"))
		
	# generate sample kernel
	# ----------------------
	ssaoKernel = []
	for i in range(64):
		sample = glm.vec3(np.random.uniform((-1, -1, 0), (1,1,1), (3, )))
		sample = glm.normalize(sample)
		sample*=np.random.uniform(0,1)
		scale = i/64

		# scale samples s.t. they are more aligned to center of kernel
		scale = glm.mix(0.1, 1.0, scale*scale)
		sample*=scale
		ssaoKernel.append(sample)

	with program.use(ssao_program):
		for i, sample in enumerate(ssaoKernel):
			name = "samples[{}]".format(i)
			location = glGetUniformLocation(ssao_program, name)
			print(name, location)
			program.set_uniform(ssao_program, name, sample)

	noise_data = np.random.uniform((-1,-1,0),(1,1,0),(4,4,3))
	noise_texture = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, noise_texture)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, 4, 4, 0, GL_RGB, GL_FLOAT, noise_data)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
	glBindTexture(GL_TEXTURE_2D, 0)

	# create ssao fbo
	# ---------------
	ssao_fbo = glGenFramebuffers(1)
	ssao_width = window.width
	ssao_height = window.height
	
	# colorbuffer
	ssao_tex = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, ssao_tex)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, ssao_width, ssao_height, 0, GL_RED, GL_FLOAT, None)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glBindTexture(GL_TEXTURE_2D, 0)

	with fbo.bind(ssao_fbo):
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, ssao_tex, 0)
		assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE


	# blur stage
	ssao_blur_fbo = glGenFramebuffers(1)

	ssao_blur_tex = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, ssao_blur_tex)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, ssao_width, ssao_height, 0, GL_RED, GL_FLOAT, None)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glBindTexture(GL_TEXTURE_2D, 0)

	with fbo.bind(ssao_blur_fbo):
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, ssao_blur_tex, 0)
		assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
		
	# main loop
	while not window.should_close():
		# ssao - geometry pass
		with fbo.bind(gBuffer):
			glViewport(0, 0, window.width, window.height)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			with program.use(ssao_geometry_program):
				program.set_uniform(ssao_geometry_program, 'projectionMatrix', window.projection_matrix)
				program.set_uniform(ssao_geometry_program, 'viewMatrix', window.view_matrix)

				# draw cube
				translation = glm.translate(glm.mat4(1), (0,0.5,0))
				rotation = glm.rotate(glm.mat4(1), 0, (0,1,0))
				scale = glm.scale(glm.mat4(1), (1,1,1))
				program.set_uniform(ssao_geometry_program, 'modelMatrix', translation*rotation*scale)
				program.set_uniform(ssao_geometry_program, 'albedo', (0.2,0.8,0.8))
				imdraw.sphere(ssao_geometry_program)

				# draw room
				translation = glm.translate(glm.mat4(1), (0,2.5,0))
				rotation = glm.rotate(glm.mat4(1), 0, (0,1,0))
				scale = glm.scale(glm.mat4(1), (10,5,10))
				program.set_uniform(ssao_geometry_program, 'modelMatrix', translation*rotation*scale)
				program.set_uniform(ssao_geometry_program, 'albedo', (0.2,0.3,0.4))
				imdraw.cube(ssao_geometry_program, flip=True)

		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		with fbo.bind(ssao_fbo):
			with program.use(ssao_program):
				program.set_uniform(ssao_program, 'projectionMatrix', window.projection_matrix)

				glActiveTexture(GL_TEXTURE0+0)
				glBindTexture(GL_TEXTURE_2D, gPosition)
				glActiveTexture(GL_TEXTURE0+1)
				glBindTexture(GL_TEXTURE_2D, gNormal)
				glActiveTexture(GL_TEXTURE0+2)
				glBindTexture(GL_TEXTURE_2D, noise_texture)

				program.set_uniform(ssao_program, 'gPosition', 0)
				program.set_uniform(ssao_program, 'gNormal', 1)
				program.set_uniform(ssao_program, 'texNoise', 2)

				imdraw.quad(ssao_program)

		with fbo.bind(ssao_blur_fbo):
			with program.use(ssao_blur_program):
				glActiveTexture(GL_TEXTURE0+0)
				glBindTexture(GL_TEXTURE_2D, ssao_tex)
				program.set_uniform(ssao_blur_program, 'ssaoInput', 0)
				imdraw.quad(ssao_blur_program)

		imdraw.texture(ssao_blur_tex, (0, 0, window.width, window.height), shuffle=(0,0,0,-1))

		window.swap_buffers()
		GLFWViewer.poll_events()