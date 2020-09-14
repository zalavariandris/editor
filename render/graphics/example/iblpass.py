from OpenGL.GL import *
import numpy as np
from editor.render.puregl import program, texture, fbo
from editor.render import glsl
from editor.render import assets
from renderpass import RenderPass
import glm
from editor.render.puregl import imdraw

from environmentpass import EnvironmentPass


class IrradiancePass(RenderPass):
	def __init__(self, width, height):
		super().__init__(width, height, False, None)

		# input
		self.environment = None

		# output
		self.irradiance = None

	@property
	def projection(self):
		return glm.perspective(glm.radians(90), 1.0,0.1,10.0)
	
	@property
	def views(self):
		return [
			glm.lookAt((0, 0, 0), ( 1,  0,  0), (0, -1,  0)),
			glm.lookAt((0, 0, 0), (-1,  0,  0), (0, -1,  0)),
			glm.lookAt((0, 0, 0), ( 0,  1,  0), (0,  0,  1)),
			glm.lookAt((0, 0, 0), ( 0, -1,  0), (0,  0, -1)),
			glm.lookAt((0, 0, 0), ( 0,  0,  1), (0, -1,  0)),
			glm.lookAt((0, 0, 0), ( 0,  0, -1), (0, -1,  0))
		]
		
	def setup(self):

		# create shader
		self.prog = program.create(*glsl.read('cubemap.vs', 'irradiance_convolution.fs'))

		# create texture
		self.irradiance = glGenTextures(1)
		glBindTexture(GL_TEXTURE_CUBE_MAP, self.irradiance)
		for i in range(6):
			glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

		# create rbo
		rbo = glGenRenderbuffers(1)
		glBindRenderbuffer(GL_RENDERBUFFER, rbo)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height)
		glBindRenderbuffer(GL_RENDERBUFFER, 0)

		# create fbo
		self.fbo = glGenFramebuffers(1)
		with fbo.bind(self.fbo):
			glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rbo)
		

	def render(self):
		assert self.environment is not None
		super().render()
		# solve irradiance map
		with program.use(self.prog):
			program.set_uniform(self.prog, "environmentMap", 0)
			program.set_uniform(self.prog, "projectionMatrix", self.projection)
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_CUBE_MAP, self.environment)

			glViewport(0, 0, self.width, self.width) # don't forget to configure the viewport to the capture dimensions.
			with fbo.bind(self.fbo):
				for i in range(6):
					program.set_uniform(self.prog, "viewMatrix", self.views[i]);
					glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, self.irradiance, 0)
					glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
					imdraw.cube(self.prog, flip=True)


class PrefilterPass(RenderPass):
	def __init__(self):
		super().__init__(128, 128, False, None)

		# input
		self.environment = None

		# output
		self.prefilter = None

	@property
	def projection(self):
		return glm.perspective(glm.radians(90), 1.0,0.1,10.0)
	
	@property
	def views(self):
		return [
			glm.lookAt((0, 0, 0), ( 1,  0,  0), (0, -1,  0)),
			glm.lookAt((0, 0, 0), (-1,  0,  0), (0, -1,  0)),
			glm.lookAt((0, 0, 0), ( 0,  1,  0), (0,  0,  1)),
			glm.lookAt((0, 0, 0), ( 0, -1,  0), (0,  0, -1)),
			glm.lookAt((0, 0, 0), ( 0,  0,  1), (0, -1,  0)),
			glm.lookAt((0, 0, 0), ( 0,  0, -1), (0, -1,  0))
		]
		
	def setup(self):

		# create shader
		self.prog = program.create(*glsl.read('cubemap.vs', 'prefilter.fs'))

		# create texture
		self.prefilter = glGenTextures(1)
		glBindTexture(GL_TEXTURE_CUBE_MAP, self.prefilter)
		for i in range(6):
			glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB32F, 128, 128, 0, GL_RGB, GL_FLOAT, None)

		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

		glGenerateMipmap(GL_TEXTURE_CUBE_MAP)

		# create rbo
		self.rbo = glGenRenderbuffers(1)
		glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height)
		glBindRenderbuffer(GL_RENDERBUFFER, 0)

		# create fbo
		self.fbo = glGenFramebuffers(1)
		# attach depth buffer
		with fbo.bind(self.fbo):
			glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.rbo)
		
	def render(self):
		super().render()
		assert self.environment is not None
		# run a quasi monte-carlo simulation on the environment lighting to create a prefilter (cube)map.
		with program.use(self.prog):
			program.set_uniform(self.prog, "environmentMap", 0)
			program.set_uniform(self.prog, "projectionMatrix", self.projection)
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_CUBE_MAP, self.environment)

			with fbo.bind(self.fbo):
				maxMipLevels = 5

				for mip in range(maxMipLevels):
					# resize framebuffer according to mip-level size.
					mipWidth  = int(128 * glm.pow(0.5, mip))
					mipHeight = int(128 * glm.pow(0.5, mip))
					glBindRenderbuffer(GL_RENDERBUFFER, self.rbo);
					glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, mipWidth, mipHeight)
					glViewport(0, 0, mipWidth, mipHeight)

					roughness = mip / (maxMipLevels - 1)
					program.set_uniform(self.prog, "roughness", roughness)

					for i in range(6):
						program.set_uniform(self.prog, "viewMatrix", self.views[i])
						glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, self.prefilter, mip)

						glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
						imdraw.cube(self.prog, flip=True)


class BRDFPass(RenderPass):
	"""
	Generate a 2D LUT from the BRDF equations used
	"""
	def __init__(self, width, height):
		super().__init__(width, height, False, GL_BACK)

	def setup(self):
		# Create Shader
		self.prog = program.create(*glsl.read('brdf'))
		
		# Create textures
		self.brdflut = glGenTextures(1)
		# pre-allocate enough memory for the LUT texture.
		glBindTexture(GL_TEXTURE_2D, self.brdflut)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RG16F, self.width, self.height, 0, GL_RG, GL_FLOAT, None);
		# be sure to set wrapping mode to GL_CLAMP_TO_EDGE
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

		# create fbo
		self.fbo = glGenFramebuffers(1)

		with fbo.bind(self.fbo):
			glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.brdflut, 0)
			assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	def render(self):
		super().render()
		# re-configure capture framebuffer object and render screen-space quad with BRDF shader.
		with program.use(self.prog):
			with fbo.bind(self.fbo):
				glViewport(0, 0, self.width, self.height)
				glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
				imdraw.quad(self.prog)

if __name__ == "__main__":
	from editor.render.window import GLFWViewer
	from editor.render.graphics.cameras import PerspectiveCamera, OrthographicCamera
	from editor.render.puregl import imdraw

	width = 1024
	height = 768
	window = GLFWViewer(width, height, (0.2, 0.2, 0.2, 1.0))
	environment_image = assets.imread('hdri/Tropical_Beach_3k.hdr')
	# environment_image = assets.imread('container2_axis.png')[...,:3]/255
	environment_pass = EnvironmentPass(512, 512)
	irradiance_pass = IrradiancePass(32,32)
	prefilter_pass = PrefilterPass()
	brdf_pass = BRDFPass(512, 512)

	with window:
		envtex = texture.create(environment_image, 0, GL_RGB)
		environment_pass.setup()
		environment_pass.texture = envtex
		environment_pass.render()
		irradiance_pass.setup()
		irradiance_pass.environment = environment_pass.cubemap
		irradiance_pass.render()
		prefilter_pass.setup()
		prefilter_pass.environment = environment_pass.cubemap
		prefilter_pass.render()
		brdf_pass.setup()
		brdf_pass.render()

	with window:
		while not window.should_close():
			

			glClearColor(0.3,0.3,0.3,1)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glDisable(GL_DEPTH_TEST)
			imdraw.texture(envtex, (0,0,190, 190), shuffle=(0,1,2,-1))
			
			# glEnable(GL_DEPTH_TEST)
			imdraw.cubemap(environment_pass.cubemap, (200,0,190, 190), window.projection_matrix, window.view_matrix)
			imdraw.cubemap(irradiance_pass.irradiance, (400,0,190, 190), window.projection_matrix, window.view_matrix)
			imdraw.cubemap(prefilter_pass.prefilter, (600,0,190, 190), window.projection_matrix, window.view_matrix)
			imdraw.texture(brdf_pass.brdflut, (800, 0, 190, 190))
			window.swap_buffers()
			GLFWViewer.poll_events()


