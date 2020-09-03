from OpenGL.GL import *
import numpy as np
import glm

from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program, fbo
from editor.render import glsl


width, height = 1024, 768
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

# Setup Scene
# ============

# lights
lights = [
	{
		'type': 0,
		'direction': glm.vec3(5, -8, -3),
		'color': glm.vec3(1.0)*1
	},
	{
		'type': 1,
		'position': glm.vec3(2, 1,3),
		'color': glm.vec3(0.66,0.35,0.2)*20
	},
	{
		'type': 2,
		'position': glm.vec3(-2, 1, -10),
		'direction': glm.vec3(2, -1, 10),
		'color': glm.vec3(0.2,0.18,0.7)*500
	},
]

with window:

	# SETUP GL
	# ========
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_CULL_FACE)

	# Geometry Pass
	# -------------
	gBuffer = glGenFramebuffers(1)
	geometry_program = program.create(*glsl.read("deferred_geometry"))
	gPosition, gNormal, gAlbedoSpecular = glGenTextures(3)

	glBindFramebuffer(GL_FRAMEBUFFER, gBuffer)
	glDrawBuffers(3, [GL_COLOR_ATTACHMENT0+0, GL_COLOR_ATTACHMENT0+1, GL_COLOR_ATTACHMENT0+2])
	for i, tex in enumerate([gPosition, gNormal, gAlbedoSpecular]):
		glBindTexture(GL_TEXTURE_2D, tex)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, None)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glFramebufferTexture2D(
			GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0+i, GL_TEXTURE_2D, tex, 0
		)
		glBindTexture(GL_TEXTURE_2D, 0)

	# create depth+stencil buffertarget, pname, param
	rbo = glGenRenderbuffers(1)
	glBindRenderbuffer(GL_RENDERBUFFER, rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
	glBindRenderbuffer(GL_RENDERBUFFER, 0)

	glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	# Lighting pass
	# -------------
	pbr_fbo = glGenFramebuffers(1)
	glBindFramebuffer(GL_FRAMEBUFFER, pbr_fbo)
	glDrawBuffers(1, [GL_COLOR_ATTACHMENT0+0])
	pbr_program = program.create(*glsl.read("deferred_pbr"))
	beautyBuffer = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, beautyBuffer)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, None)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	glFramebufferTexture2D(
		GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, beautyBuffer, 0
	)
	glBindTexture(GL_TEXTURE_2D, 0)

	# create depth+stencil buffer
	rbo = glGenRenderbuffers(1)
	glBindRenderbuffer(GL_RENDERBUFFER, rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
	glBindRenderbuffer(GL_RENDERBUFFER, 0)

	glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	# Bloom pass
	# ----------

	## Cutoff
	bloom_program = program.create(*glsl.read("debug_quad.vs", "cutoff_highlights.fs"))
	bloom_fbo = glGenFramebuffers(1)
	bloom_tex = glGenTextures(1)
	blur_pingpong_tex = glGenTextures(2)

	glBindTexture(GL_TEXTURE_2D, bloom_tex)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, None)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	glBindTexture(GL_TEXTURE_2D, 0)

	glBindFramebuffer(GL_FRAMEBUFFER, bloom_fbo)
	glFramebufferTexture2D(
		GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, bloom_tex, 0
	)

	# create depth+stencil buffer
	rbo = glGenRenderbuffers(1)
	glBindRenderbuffer(GL_RENDERBUFFER, rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
	glBindRenderbuffer(GL_RENDERBUFFER, 0)

	glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	## Blur
	blur_program = program.create(*glsl.read("debug_quad.vs", "gaussianblur.fs"))
	blur_fbo = glGenFramebuffers(1)
	blur_pingpong = glGenTextures(2)
	for blur_tex in blur_pingpong:
		glBindTexture(GL_TEXTURE_2D, blur_tex)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, None)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glBindTexture(GL_TEXTURE_2D, 0)

	glBindFramebuffer(GL_FRAMEBUFFER, blur_fbo)
	glFramebufferTexture2D(
		GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, blur_pingpong[0], 0
	)

	# create depth+stencil buffer
	rbo = glGenRenderbuffers(1)
	glBindRenderbuffer(GL_RENDERBUFFER, rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
	glBindRenderbuffer(GL_RENDERBUFFER, 0)

	glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	# Tonemapping pass
	# ----------------
	tonemapping_program = program.create(*glsl.read("tonemapping"))
	tonemapping_fbo = glGenFramebuffers(1)
	glBindFramebuffer(GL_FRAMEBUFFER, tonemapping_fbo)
	tonemapping_color = glGenTextures(1)

	glBindTexture(GL_TEXTURE_2D, tonemapping_color)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, None)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	glFramebufferTexture2D(
		GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tonemapping_color, 0
	)
	glBindTexture(GL_TEXTURE_2D, 0)

	# create depth+stencil buffer
	rbo = glGenRenderbuffers(1)
	glBindRenderbuffer(GL_RENDERBUFFER, rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
	glBindRenderbuffer(GL_RENDERBUFFER, 0)

	## attach depth and stencil component
	glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
	
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
	glBindFramebuffer(GL_FRAMEBUFFER, 0)


with window:
	while not window.should_close():
		# DRAW GL
		# =======

		# Geometry Pass
		# -------------
		with fbo.bind(gBuffer), program.use(geometry_program) as prog:
			glViewport(0,0, window.width, window.height);
			glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
				
			program.set_uniform(prog, "projection", window.projection_matrix)
			program.set_uniform(prog, "view", window.view_matrix)

			# draw cube
			model_matrix = glm.translate(glm.mat4(1), (-1,0.5,0))
			program.set_uniform(prog, 'model', model_matrix)

			imdraw.cube(prog)

			# draw sphere
			model_matrix = glm.translate(glm.mat4(1), (1,0.5,0))
			program.set_uniform(prog, 'model', model_matrix)
			imdraw.sphere(prog)

			# draw groundplane
			model_matrix = glm.translate(glm.mat4(1), (0,0.0,0))
			program.set_uniform(prog, 'model', model_matrix)
			imdraw.plane(prog)

		# Lighting Pass
		# -------------
		with fbo.bind(pbr_fbo), program.use(pbr_program):
			glViewport(0,0,window.width, window.height)
			glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

			# set matrices (this is redundant as we are simple drawing a textured quad on screen)
			program.set_uniform(pbr_program, "projection", np.eye(4))
			program.set_uniform(pbr_program, "view", np.eye(4))
			program.set_uniform(pbr_program, "model", np.eye(4))

			camera_pos = glm.inverse(window.view_matrix)[3].xyz
			program.set_uniform(pbr_program, 'cameraPos', camera_pos)
			program.set_uniform(pbr_program, "view", np.eye(4))

			# upload gBuffer
			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_2D, gPosition)
			glActiveTexture(GL_TEXTURE0+1)
			glBindTexture(GL_TEXTURE_2D, gNormal)
			glActiveTexture(GL_TEXTURE0+2)
			glBindTexture(GL_TEXTURE_2D, gAlbedoSpecular)
			program.set_uniform(pbr_program, "gPosition", 0)
			program.set_uniform(pbr_program, "gNormal", 1)
			program.set_uniform(pbr_program, "gAlbedoSpecular", 2)

			# upload lights
			for i, light in enumerate(lights):
				lightPos = light.get('position', glm.vec3(0))
				# lightPos = window.view_matrix*glm.vec4(lightPos,1.0)
				# lightPos = lightPos.xyz;

				lightDir = light.get('direction', glm.vec3(0))
				# lightDir = glm.transpose(glm.inverse(glm.mat3(window.view_matrix))) * lightDir

				program.set_uniform(pbr_program, "lights[{}].type".format(i), light['type'])
				program.set_uniform(pbr_program, "lights[{}].position".format(i), lightPos)
				program.set_uniform(pbr_program, "lights[{}].direction".format(i), lightDir)
				program.set_uniform(pbr_program, "lights[{}].color".format(i), light['color'])

			# draw quad
			imdraw.quad(pbr_program)

		# Bloom pass
		# ----------
		# cutoff highlights
		with fbo.bind(bloom_fbo), program.use(bloom_program) as prog:
			glViewport(0,0,window.width, window.height)
			glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_2D, beautyBuffer)

			program.set_uniform(prog, 'screenTexture', 0)

			imdraw.quad(prog)

		# # blur highlights
		# with fbo.bind(blur_fbo), program.use(blur_program) as prog:
		# 	glViewport(0,0,window.width, window.height)
		# 	glClearColor(0,0,0,0)
		# 	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		# 	iterations=10
		# 	for i in range(iterations):
		# 		glActiveTexture(GL_TEXTURE0+0)
		# 		glBindTexture(GL_TEXTURE_2D, bloom_tex if i==0 else blur_pingpong_tex[i%2])
		# 		glFramebufferTexture2D(
		# 			GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, blur_pingpong_tex[int((i+1)%2)], 0
		# 		)
		# 		program.set_uniform(prog, 'screenTexture', 0)

		# 		imdraw.quad(prog)



		# Tonemapping pass
		# ----------------
		with fbo.bind(tonemapping_fbo), program.use(tonemapping_program) as prog:
			glViewport(0,0,window.width, window.height)
			glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

			program.set_uniform(prog, "projectionMatrix", np.eye(4)) # redundant
			program.set_uniform(prog, "viewMatrix", np.eye(4))
			program.set_uniform(prog, "modelMatrix", np.eye(4))

			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_2D, beautyBuffer)
			glActiveTexture(GL_TEXTURE0+1)
			glBindTexture(GL_TEXTURE_2D, 0)

			program.set_uniform(prog, 'screenTexture', 0)
			program.set_uniform(prog, 'bloomBlur', 1)
			program.set_uniform(prog, 'exposure', 0.0)
			program.set_uniform(prog, 'gamma', 2.2)

			imdraw.quad(prog)

		# Display
		# -------
		glViewport(0,0,window.width,window.height);
		glClearColor(*window._clear_color)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		imdraw.texture(gPosition,         (  0,   0, 90, 90))
		imdraw.texture(gNormal,           (100,   0, 90, 90))
		imdraw.texture(gAlbedoSpecular,   (200,   0, 90, 90), shuffle=(0,1,2,-1))
		imdraw.texture(gAlbedoSpecular,   (300,   0, 90, 90), shuffle=(3,3,3,-1))

		imdraw.texture(beautyBuffer,      (  0, 100, 90, 90), shuffle=(0,1,2,-1))
		imdraw.texture(bloom_tex,         (100, 100, 90, 90), shuffle=(0,1,2,-1))
		imdraw.texture(blur_pingpong_tex[0],         (200, 100, 90, 90), shuffle=(0,1,2,-1))

		imdraw.texture(tonemapping_color, (0,0,window.width, window.height))

		window.swap_buffers()
		GLFWViewer.poll_events()