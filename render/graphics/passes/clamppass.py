from editor.render.graphics.passes import RenderPass
from OpenGL.GL import *
from editor.render import puregl, glsl, imdraw


class ClampPass(RenderPass):
	def __init__(self, width, height):
		super().__init__(width, height, False, GL_BACK)
		self.program = None
		self.output_texture = None
		self.fbo = None

	def setup(self):
		super().setup()
		# create program
		self.program = puregl.program.create(*glsl.read("graphics/clamp"))

		# create texture
		self.output_texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.output_texture)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glBindTexture(GL_TEXTURE_2D, 0)

		# create depth+stencil buffer
		rbo = glGenRenderbuffers(1)
		glBindRenderbuffer(GL_RENDERBUFFER, rbo)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
		glBindRenderbuffer(GL_RENDERBUFFER, 0)

		# create fbo
		self.fbo = glGenFramebuffers(1)
		with puregl.fbo.bind(self.fbo):
			glFramebufferTexture2D(
				GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.output_texture, 0
			)
			# attach depth and stencil component
			glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
			
			assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	def render(self, input_texture, minimum, maximum):
		super().render()
		glCullFace(GL_BACK)
		glDisable(GL_DEPTH_TEST)
		with puregl.fbo.bind(self.fbo), puregl.program.use(self.program) as prog:
			glViewport(0,0,self.width, self.height)
			glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_2D, input_texture)

			puregl.program.set_uniform(prog, 'screenTexture', 0)
			puregl.program.set_uniform(prog, 'minimum', float(minimum))
			puregl.program.set_uniform(prog, 'maximum', float(maximum))

			imdraw.quad(prog)

		return self.output_texture

if __name__ == "__main__":
	import numpy as np
	from editor.render import assets
	from editor.render.graphics.examples.viewer import Viewer
	imgA = assets.imread("peppers.png").astype(np.float32)[...,:3]/255

	clamppass = ClampPass(512, 512)

	viewer = Viewer()
	@viewer.event
	def on_setup():
		global texA
		texA = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texA)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, imgA.shape[1], imgA.shape[0], 0, GL_RGB, GL_FLOAT, imgA)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glBindTexture(GL_TEXTURE_2D, 0)

	@viewer.event
	def on_draw():
		imdraw.texture(texA, (0,0,200,200))
		added = clamppass.render(texA, 0.5, 1.0)
		imdraw.texture(added, (400,0,500,500))
	viewer.start()