from OpenGL.GL import *
import numpy as np
import glm

from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program, fbo, texture
from editor.render import glsl
from editor.render import assets

width, height = 1024, 768
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

# Setup Scene
# ============

class DirectionalLight:
	def __init__(self, direction, color, position, radius, near, far):
		self.direction = direction
		self.color = color
		self.position = position
		self.radius = radius
		self.near = near
		self.far = far

	@property
	def projection(self):
		return glm.ortho(-self.radius,self.radius,-self.radius,self.radius, self.near, self.far)
			
	@property	
	def view(self):
		return glm.lookAt(self.position, self.position+self.direction, (0,1,0))


class Spotlight:
	def __init__(self, position, direction, color, fov, near, far):
		self.position = position
		self.direction = direction
		self.color = color
		self.fov = fov
		self.near = near
		self.far = far

	@property
	def projection(self):
		aspect = 1.0
		return glm.perspective(glm.radians(self.fov), aspect,self.near,self.far)
			
	@property	
	def view(self):
		return glm.lookAt(self.position, self.position+self.direction, (0,1,0))

	@property
	def cut_off(self):
		return glm.cos(glm.radians(self.fov/2))


class Pointlight:
	def __init__(self, position, color, near, far):
		self.position = position
		self.color = color
		self.near = near
		self.far = far

	@property
	def projection(self):
		aspect = 1.0
		return glm.perspective(glm.radians(90.0), aspect, self.near, self.far)
	

	@property
	def views(self):
		shadowTransforms = []
		shadowTransforms.append(glm.lookAt(pointlight.position, pointlight.position + glm.vec3( 1, 0, 0), glm.vec3(0,-1, 0)))
		shadowTransforms.append(glm.lookAt(pointlight.position, pointlight.position + glm.vec3(-1, 0, 0), glm.vec3(0,-1, 0)))
		shadowTransforms.append(glm.lookAt(pointlight.position, pointlight.position + glm.vec3( 0, 1, 0), glm.vec3(0, 0, 1)))
		shadowTransforms.append(glm.lookAt(pointlight.position, pointlight.position + glm.vec3( 0,-1, 0), glm.vec3(0, 0,-1)))
		shadowTransforms.append(glm.lookAt(pointlight.position, pointlight.position + glm.vec3( 0, 0, 1), glm.vec3(0,-1, 0)))
		shadowTransforms.append(glm.lookAt(pointlight.position, pointlight.position + glm.vec3( 0, 0,-1), glm.vec3(0,-1, 0)))

		shadowTransforms = np.array([np.array(m) for m in shadowTransforms])
		return shadowTransforms
	

dirlight = DirectionalLight(direction=glm.vec3(5,-8,-3),
	                        color=glm.vec3(1.0)*1.0,
	                        position=glm.vec3(-5, 8, 3),
	                        radius=5.0,
	                        near=1.0,
	                        far=30)

spotlight = Spotlight(position=glm.vec3(-2, 1.1, -10),
	                  direction=glm.vec3(2, -1.1, 10),
	                  color=glm.vec3(0.2, 0.18, 0.7)*150,
	                  fov=30.0,
	                  near=0.1,
	                  far=13.0)

pointlight = Pointlight(position=glm.vec3(5, 2, 0.5),
	                    color=glm.vec3(1, 0.7, 0.1)*30,
	                    near=1.0,
	                    far=8.0)

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

	# Shadowmap Pass setup
	# --------------------
	depth_program = program.create(*glsl.read("simple_depth"))
	
	## dirlight
	dirlight_fbo = glGenFramebuffers(1)
	dirlight_shadowmap = glGenTextures(1)
	dirlight_shadowsize = 1024, 1024

	glBindTexture(GL_TEXTURE_2D, dirlight_shadowmap)
	glTexImage2D(
		GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, *dirlight_shadowsize, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None
	)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
	glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array([1,1,1,1]))
	
	glBindTexture(GL_TEXTURE_2D, 0)

	with fbo.bind(dirlight_fbo):
		# dont render color data
		glDrawBuffer(GL_NONE)
		glReadBuffer(GL_NONE)

		#attach depth component
		glFramebufferTexture2D(
			GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, dirlight_shadowmap, 0
		)
		assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	## spotlight shadow setup
	spotlight_fbo = glGenFramebuffers(1)
	spotlight_shadowmap = glGenTextures(1)
	spotlight_shadowsize = 1024, 1024
	glBindTexture(GL_TEXTURE_2D, spotlight_shadowmap)
	glTexImage2D(
		GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, spotlight_shadowsize[0], spotlight_shadowsize[1], 0, GL_DEPTH_COMPONENT, GL_FLOAT, None
	)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
	glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array([1,1,1,1]))
	
	glBindTexture(GL_TEXTURE_2D, 0)

	with fbo.bind(spotlight_fbo):
		# dont render color data
		glDrawBuffer(GL_NONE)
		glReadBuffer(GL_NONE)

		#attach depth component
		glFramebufferTexture2D(
			GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, spotlight_shadowmap, 0
		)
		assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
		
	# Point Shadow Pass setup
	# -----------------
	pointlight_shadowfbo = glGenFramebuffers(1)
	pointlight_shadowsize = 1024, 1024
	# create depth cubemap texture
	pointlight_shadowcube = glGenTextures(1)
	glActiveTexture(GL_TEXTURE0+6+2)
	glBindTexture(GL_TEXTURE_CUBE_MAP, pointlight_shadowcube)

	for i in range(6):
		glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, 0, GL_DEPTH_COMPONENT,
			pointlight_shadowsize[0], pointlight_shadowsize[1], 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)

	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
	

	# attach cubemap to fbo depth attachment
	glBindFramebuffer(GL_FRAMEBUFFER, pointlight_shadowfbo);
	glFramebufferTexture(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, pointlight_shadowcube, 0)
	glDrawBuffer(GL_NONE)
	glReadBuffer(GL_NONE)
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	# create shader
	point_shadow_program = program.create(*glsl.read("point_shadow"))


	# Environment pass
	# ----------------
	## Create environment texture
	environment_data = assets.imread('hdri/Tropical_Beach_3k.hdr')
	environment_data = assets.to_linear(environment_data)

	env_height, env_width, env_channels = environment_data.shape
	environment_tex = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, environment_tex)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, env_width, env_height, 0, GL_RGB, GL_FLOAT, environment_data)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

	## Capture environment map to cubemap
	# create cubemap texture
	env_cubemap = glGenTextures(1)
	equirectangular_to_cubemap_program = program.create(*glsl.read('cubemap.vs', 'equirectangular_to_cubemap.fs'))
	env_height, env_width, env_channels = environment_data.shape
	
	env_width, env_height = 512, 512
	glBindTexture(GL_TEXTURE_CUBE_MAP, env_cubemap)
	for i in range(6):
		glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, 0, GL_RGB32F, env_width, env_height,0,GL_RGB, GL_FLOAT, None)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

	# setup cubemap projections to render each face
	capture_projection = glm.perspective(glm.radians(90), 1.0,0.1,10.0)
	capture_views = [
		glm.lookAt((0, 0, 0), ( 1,  0,  0), (0, -1,  0)),
		glm.lookAt((0, 0, 0), (-1,  0,  0), (0, -1,  0)),
		glm.lookAt((0, 0, 0), ( 0,  1,  0), (0,  0,  1)),
		glm.lookAt((0, 0, 0), ( 0, -1,  0), (0,  0, -1)),
		glm.lookAt((0, 0, 0), ( 0,  0,  1), (0, -1,  0)),
		glm.lookAt((0, 0, 0), ( 0,  0, -1), (0, -1,  0))
	]

	# create rbo
	capture_rbo = glGenRenderbuffers(1)
	glBindRenderbuffer(GL_RENDERBUFFER, capture_rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, env_width, env_height)
	glBindRenderbuffer(GL_RENDERBUFFER, 0)

	# create cubemap fbo
	capture_fbo = glGenFramebuffers(1)
	# attach depth buffer
	with fbo.bind(capture_fbo):
		glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, capture_rbo)
		
	# draw environment map to each cubemap side
	glViewport(0,0,env_width,env_height)
	glActiveTexture(GL_TEXTURE0)
	glBindTexture(GL_TEXTURE_2D, environment_tex)
	with program.use(equirectangular_to_cubemap_program):
		program.set_uniform(equirectangular_to_cubemap_program, "equirectangularMap", 0)
		program.set_uniform(equirectangular_to_cubemap_program, "projectionMatrix", capture_projection)

		
		with fbo.bind(capture_fbo):
			for i in range(6):
				glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, env_cubemap, 0)	
				program.set_uniform(equirectangular_to_cubemap_program, "viewMatrix", capture_views[i])
				glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
				imdraw.cube(equirectangular_to_cubemap_program, flip=True)

	## setup skybox drawing
	skybox_program = program.create(*glsl.read('skybox'))

	# IBL pass
	# --------
	## Create irradiance cubemap for diffuse IBL
	irradiance_program = program.create(*glsl.read('cubemap.vs', 'irradiance_convolution.fs'))

	irradiance_map = glGenTextures(1)
	glBindTexture(GL_TEXTURE_CUBE_MAP, irradiance_map);
	for i in range(6):
		glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB32F, 32, 32, 0, GL_RGB, GL_FLOAT, None)

	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

	glBindRenderbuffer(GL_RENDERBUFFER, capture_rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, 32, 32)
	glBindRenderbuffer(GL_RENDERBUFFER, 0)

	# solve irradiance map
	with program.use(irradiance_program):
		program.set_uniform(irradiance_program, "environmentMap", 0)
		program.set_uniform(irradiance_program, "projectionMatrix", capture_projection)
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_CUBE_MAP, env_cubemap)

		glViewport(0, 0, 32, 32) # don't forget to configure the viewport to the capture dimensions.
		with fbo.bind(capture_fbo):
			for i in range(6):
				program.set_uniform(irradiance_program, "viewMatrix", capture_views[i]);
				glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, irradiance_map, 0)
				glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

				imdraw.cube(irradiance_program, flip=True)

	## Create Prefilter cubemap for specular IBL
	prefilterShader = program.create(*glsl.read('cubemap.vs', 'prefilter.fs'))

	prefilterMap = glGenTextures(1)
	glBindTexture(GL_TEXTURE_CUBE_MAP, prefilterMap)
	for i in range(6):
		glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB32F, 128, 128, 0, GL_RGB, GL_FLOAT, None)

	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

	glGenerateMipmap(GL_TEXTURE_CUBE_MAP)

	# run a quasi monte-carlo simulation on the environment lighting to create a prefilter (cube)map.
	with program.use(prefilterShader):
		program.set_uniform(prefilterShader, "environmentMap", 0)
		program.set_uniform(prefilterShader, "projectionMatrix", capture_projection)
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_CUBE_MAP, env_cubemap)

		with fbo.bind(capture_fbo):
			maxMipLevels = 5

			for mip in range(maxMipLevels):
				# resize framebuffer according to mip-level size.
				mipWidth  = int(128 * glm.pow(0.5, mip))
				mipHeight = int(128 * glm.pow(0.5, mip))
				glBindRenderbuffer(GL_RENDERBUFFER, capture_rbo);
				glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, mipWidth, mipHeight)
				glViewport(0, 0, mipWidth, mipHeight)

				roughness = mip / (maxMipLevels - 1)
				program.set_uniform(prefilterShader, "roughness", roughness)

				for i in range(6):
					program.set_uniform(prefilterShader, "viewMatrix", capture_views[i])
					glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, prefilterMap, mip)

					glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
					imdraw.cube(prefilterShader, flip=True)

	## Generate a 2D LUT from the BRDF equations used
	brdfShader = program.create(*glsl.read('brdf'))
	brdfLUTTexture = glGenTextures(1)

	# pre-allocate enough memory for the LUT texture.
	glBindTexture(GL_TEXTURE_2D, brdfLUTTexture)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RG16F, 512, 512, 0, GL_RG, GL_FLOAT, None);
	# be sure to set wrapping mode to GL_CLAMP_TO_EDGE
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

	# re-configure capture framebuffer object and render screen-space quad with BRDF shader.
	with fbo.bind(capture_fbo):
		glBindRenderbuffer(GL_RENDERBUFFER, capture_rbo)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, 512, 512)
		glBindRenderbuffer(GL_RENDERBUFFER, 0)
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, brdfLUTTexture, 0)

	with program.use(brdfShader):
		with fbo.bind(capture_fbo):
			glViewport(0, 0, 512, 512)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			imdraw.quad(brdfShader)

	# Lighting pass setup
	# -------------------
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
	## cutoff highlights
	highlights_program = program.create(*glsl.read("debug_quad.vs", "cutoff_highlights.fs"))
	highlights_fbo = glGenFramebuffers(1)
	highlights_tex = glGenTextures(1)

	glBindTexture(GL_TEXTURE_2D, highlights_tex)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, None)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	glBindTexture(GL_TEXTURE_2D, 0)

	glBindFramebuffer(GL_FRAMEBUFFER, highlights_fbo)
	glFramebufferTexture2D(
		GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, highlights_tex, 0
	)

	glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	## Blur higlights
	blur_program = program.create(*glsl.read('gaussian'))

	bloom_blur_fbos = glGenFramebuffers(2)
	bloom_blur_texs = glGenTextures(2)
	SCR_WIDTH, SCR_HEIGHT = width, height
	for i in range(2):
		glBindFramebuffer(GL_FRAMEBUFFER, bloom_blur_fbos[i])
		glBindTexture(GL_TEXTURE_2D, bloom_blur_texs[i])
		glTexImage2D(
			GL_TEXTURE_2D, 0, GL_RGBA32F, SCR_WIDTH, SCR_HEIGHT, 0, GL_RGBA, GL_FLOAT, None
		)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glFramebufferTexture2D(
			GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, bloom_blur_texs[i], 0
		)

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

	# attach depth and stencil component
	glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
	
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
	glBindFramebuffer(GL_FRAMEBUFFER, 0)


with window:
	while not window.should_close():
		# animate lights
		import math, time
		spotlight.position = glm.vec3(math.cos(time.time()*3)*4, 0.3, -4)
		spotlight.direction = -spotlight.position

		pointlight.position = glm.vec3(math.cos(time.time())*4, 1.0, math.sin(time.time())*4)

		# DRAW GL
		# =======

		# Geometry Pass
		# -------------
		glCullFace(GL_BACK)
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

		# Shadowmap Pass draw
		# -------------------
		glCullFace(GL_FRONT)
		import math, time

		## dirlight
		with fbo.bind(dirlight_fbo), program.use(depth_program) as prog:
			glViewport(0,0,*dirlight_shadowsize)
			glClear(GL_DEPTH_BUFFER_BIT)
			
			program.set_uniform(prog, "projection", dirlight.projection)
			program.set_uniform(prog, "view", dirlight.view)

			# Draw Scene
			## draw cube
			model_matrix = glm.translate(glm.mat4(1), (-1,0.5,0))
			program.set_uniform(prog, 'model', model_matrix)
			imdraw.cube(prog)

			## draw sphere
			model_matrix = glm.translate(glm.mat4(1), (1,0.5,0))
			program.set_uniform(prog, 'model', model_matrix)
			imdraw.sphere(prog)

			## draw groundplane
			model_matrix = glm.translate(glm.mat4(1), (0,0,0))
			program.set_uniform(prog, 'model', model_matrix)
			imdraw.plane(prog)

		## spotlight
		with fbo.bind(spotlight_fbo), program.use(depth_program) as prog:
			glViewport(0,0,*spotlight_shadowsize)
			glClear(GL_DEPTH_BUFFER_BIT)
			
			program.set_uniform(prog, "projection", spotlight.projection)
			program.set_uniform(prog, "view", spotlight.view)

			# Draw Scene
			## draw cube
			model_matrix = glm.translate(glm.mat4(1), (-1,0.5,0))
			program.set_uniform(prog, 'model', model_matrix)
			imdraw.cube(prog)

			## draw sphere
			model_matrix = glm.translate(glm.mat4(1), (1,0.5,0))
			program.set_uniform(prog, 'model', model_matrix)
			imdraw.sphere(prog)

			## draw groundplane
			model_matrix = glm.translate(glm.mat4(1), (0,0,0))
			program.set_uniform(prog, 'model', model_matrix)
			imdraw.plane(prog)

		# shadow depth cubemap pass
		# -------------------------
		with fbo.bind(pointlight_shadowfbo), program.use(point_shadow_program) as prog:
			glViewport(0, 0, *pointlight_shadowsize);
			glClear(GL_DEPTH_BUFFER_BIT)
			for i in range(6):
				program.set_uniform(prog, "shadowMatrices[{}]".format(i), pointlight.projection*pointlight.views[i])
			program.set_uniform(prog, 'farPlane', pointlight.far)
			program.set_uniform(prog, 'lightPos', pointlight.position)

			# Draw Scene
			## draw cube
			model_matrix = glm.translate(glm.mat4(1), (-1,0.5,0))
			program.set_uniform(prog, 'model', model_matrix)
			imdraw.cube(prog)

			## draw sphere
			model_matrix = glm.translate(glm.mat4(1), (1,0.5,0))
			program.set_uniform(prog, 'model', model_matrix)
			imdraw.sphere(prog)

			## draw groundplane
			model_matrix = glm.translate(glm.mat4(1), (0,0,0))
			program.set_uniform(prog, 'model', model_matrix)
			imdraw.plane(prog)

		# Lighting Pass draw
		# ------------------
		glCullFace(GL_BACK)
		with fbo.bind(pbr_fbo), program.use(pbr_program):
			glViewport(0,0,window.width, window.height)
			# glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

			# set matrices (this is redundant as we are simple drawing a textured quad on screen)
			program.set_uniform(pbr_program, "projection", np.eye(4))
			program.set_uniform(pbr_program, "view", np.eye(4))
			program.set_uniform(pbr_program, "model", np.eye(4))

			camera_pos = glm.inverse(window.view_matrix)[3].xyz
			program.set_uniform(pbr_program, 'cameraPos', camera_pos)

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

			# ambient lighting
			glActiveTexture(GL_TEXTURE0+3)
			glBindTexture(GL_TEXTURE_CUBE_MAP, irradiance_map)
			glActiveTexture(GL_TEXTURE0+4)
			glBindTexture(GL_TEXTURE_CUBE_MAP, prefilterMap)
			glActiveTexture(GL_TEXTURE0+5)
			glBindTexture(GL_TEXTURE_2D, brdfLUTTexture)
			program.set_uniform(pbr_program, 'irradianceMap', 3)
			program.set_uniform(pbr_program, 'prefilterMap', 4)
			program.set_uniform(pbr_program, 'brdfLUT', 5)

			# set lights uniform
			## dirlight
			program.set_uniform(pbr_program, "lights[0].type", 0)
			program.set_uniform(pbr_program, "lights[0].direction", dirlight.direction)
			program.set_uniform(pbr_program, "lights[0].color", dirlight.color)
			glActiveTexture(GL_TEXTURE0+6+0)
			glBindTexture(GL_TEXTURE_2D, dirlight_shadowmap)
			program.set_uniform(pbr_program, 'lights[0].matrix', dirlight.projection * dirlight.view)
			program.set_uniform(pbr_program, 'lights[0].shadowIdx', 0)
			program.set_uniform(pbr_program, 'shadowMaps[0]', 6+0)

			## spotlight
			program.set_uniform(pbr_program, "lights[1].type", 1)
			program.set_uniform(pbr_program, "lights[1].position", spotlight.position)
			program.set_uniform(pbr_program, "lights[1].direction", spotlight.direction)
			program.set_uniform(pbr_program, "lights[1].color", spotlight.color)
			program.set_uniform(pbr_program, "lights[1].cutOff", spotlight.cut_off)
			glActiveTexture(GL_TEXTURE0+6+1)
			glBindTexture(GL_TEXTURE_2D, spotlight_shadowmap)
			program.set_uniform(pbr_program, 'lights[1].matrix', spotlight.projection * spotlight.view)
			program.set_uniform(pbr_program, 'lights[1].shadowIdx', 1)
			program.set_uniform(pbr_program, 'shadowMaps[1]', 6+1)

			## pointlight
			program.set_uniform(pbr_program, "lights[2].type", 2)
			program.set_uniform(pbr_program, "lights[2].position", pointlight.position)
			program.set_uniform(pbr_program, "lights[2].color", pointlight.color)
			glActiveTexture(GL_TEXTURE0+6+2)
			glBindTexture(GL_TEXTURE_CUBE_MAP, pointlight_shadowcube)

			program.set_uniform(pbr_program, 'lights[2].farPlane', pointlight.far)
			program.set_uniform(pbr_program, 'lights[2].shadowIdx', 0)
			program.set_uniform(pbr_program, 'shadowCubes[0]', 6+2)

			# draw quad
			imdraw.quad(pbr_program)

		# FORWARD SHADING
		# ===============
		## Copy depth from geometry pass
		glBindFramebuffer(GL_READ_FRAMEBUFFER, gBuffer)
		glBindFramebuffer(GL_DRAW_FRAMEBUFFER, pbr_fbo) # write to default framebuffer
		glBlitFramebuffer(
		  0, 0, width, height, 0, 0, width, height, GL_DEPTH_BUFFER_BIT, GL_NEAREST
		);
		glBindFramebuffer(GL_FRAMEBUFFER, 0);
		with fbo.bind(pbr_fbo):
			# Environment Pass
			# ----------------
			glViewport(0,0,window.width,window.height);
			glDepthFunc(GL_LEQUAL)
			glDepthMask(GL_FALSE)
			
			with program.use(skybox_program):
				program.set_uniform(skybox_program, 'projection', window.projection_matrix)
				sky_view = glm.mat4(glm.mat3(window.view_matrix)); 
				program.set_uniform(skybox_program, 'view', sky_view)
				camera_pos = glm.transpose(glm.transpose(glm.inverse(window.view_matrix)))[3].xyz
				program.set_uniform(skybox_program, 'cameraPos', camera_pos)
				program.set_uniform(skybox_program, 'skybox', 0)
				program.set_uniform(skybox_program, 'groundProjection', True)
				glActiveTexture(GL_TEXTURE0+0)
				glBindTexture(GL_TEXTURE_CUBE_MAP, env_cubemap)
				imdraw.cube(skybox_program, flip=True)
			glDepthMask(GL_TRUE)
			glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

		# Bloom pass
		# ----------
		# cutoff highlights
		with fbo.bind(highlights_fbo), program.use(highlights_program) as prog:
			glViewport(0,0,window.width, window.height)
			glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_2D, beautyBuffer)

			program.set_uniform(prog, 'screenTexture', 0)

			imdraw.quad(prog)

		# blur highlights
		blur_iterations = 4
		horizontal=True
		first_iteration=True
		with program.use(blur_program):
			for i in range(blur_iterations):
				horizontal = i%2
				glBindFramebuffer(GL_FRAMEBUFFER, bloom_blur_fbos[horizontal])
				glClearColor(0.0,0.0,0.0,1.0)
				program.set_uniform(blur_program, 'horizontal', horizontal)
				glActiveTexture(GL_TEXTURE0)
				glBindTexture(
					GL_TEXTURE_2D, highlights_tex if first_iteration else bloom_blur_texs[1-horizontal]
				)
				imdraw.quad(blur_program)
				if first_iteration:
					first_iteration=False

		glBindFramebuffer(GL_FRAMEBUFFER, 0)

		glViewport(0,0,window.width, window.height)
		glClearColor(0,0,0,0)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		# Tonemapping pass
		# ----------------
		with fbo.bind(tonemapping_fbo), program.use(tonemapping_program) as prog:
			glViewport(0,0,window.width, window.height)
			glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_2D, beautyBuffer)
			glActiveTexture(GL_TEXTURE0+1)
			glBindTexture(GL_TEXTURE_2D, bloom_blur_texs[0])

			program.set_uniform(prog, 'screenTexture', 0)
			program.set_uniform(prog, 'bloomBlur', 1)
			program.set_uniform(prog, 'exposure', 1.0)
			program.set_uniform(prog, 'gamma', 2.2)

			imdraw.quad(prog)

		# Display
		# -------
		# display AOVs
		glViewport(0,0,window.width,window.height);
		glClearColor(*window._clear_color)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		# display composite
		imdraw.texture(tonemapping_color, (0, 0, window.width, window.height))

		# display AOVs
		imdraw.texture(gPosition,           (  0,   0, 90, 90))
		imdraw.texture(gNormal,             (100,   0, 90, 90))
		imdraw.texture(gAlbedoSpecular,     (200,   0, 90, 90), shuffle=(0,1,2,-1))
		imdraw.texture(gAlbedoSpecular,     (300,   0, 90, 90), shuffle=(3,3,3,-1))

		imdraw.texture(beautyBuffer,        (  0, 100, 90, 90), shuffle=(0,1,2,-1))
		imdraw.texture(highlights_tex,      (100, 100, 90, 90), shuffle=(0,1,2,-1))
		imdraw.texture(bloom_blur_texs[1],  (200, 100, 90, 90), shuffle=(0,1,2,-1))

		imdraw.texture(dirlight_shadowmap,  (  0, 200, 90, 90), shuffle=(0,0,0,-1))
		imdraw.texture(spotlight_shadowmap, (100, 200, 90, 90), shuffle=(0,0,0,-1))

		window.swap_buffers()
		GLFWViewer.poll_events()