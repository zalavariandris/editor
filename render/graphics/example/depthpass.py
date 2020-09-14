from OpenGL.GL import *
import numpy as np
from editor.render.puregl import program, texture, fbo
from editor.render import glsl
from renderpass import RenderPass


class DepthPass(RenderPass):
	def __init__(self, width, height, cull_face, draw_scene):
		super().__init__( width, height, True, cull_face)
		self.draw_scene = draw_scene

	def setup(self):
		# create program
		# --------------
		self.prog = program.create(*glsl.read("simple_depth"))

		# create textures
		# ---------------
		self.texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.texture)
		glTexImage2D(
			GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, self.width, self.height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None
		)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
		glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array([1,1,1,1]))
		
		glBindTexture(GL_TEXTURE_2D, 0)

		# crate fbo
		# ---------
		self.fbo = glGenFramebuffers(1)
		with fbo.bind(self.fbo):
			# dont render color data
			glDrawBuffer(GL_NONE)
			glReadBuffer(GL_NONE)

			#attach depth component
			glFramebufferTexture2D(
				GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.texture, 0
			)
			assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	def render(self):
		super().render()

		with fbo.bind(self.fbo), program.use(self.prog):
			# set viewport
			glViewport(0,0, self.width, self.height)

			# clear fbo
			# glClearColor(0,0,0,0)
			glClear(GL_DEPTH_BUFFER_BIT)

			# configure shaders

			# draw scene
			program.set_uniform(self.prog, "projection", self.camera.projection)
			program.set_uniform(self.prog, "view", self.camera.view)
			self.draw_scene(self.prog)



if __name__ == "__main__":
	import glm
	from editor.render.window import GLFWViewer
	from editor.render.graphics.cameras import PerspectiveCamera, OrthographicCamera
	from editor.render.puregl import imdraw
	def draw_scene(prog):
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

	width = 512
	height = 512
	window = GLFWViewer(width*2, height, (0.2, 0.2, 0.2, 1.0))
	orthoDepthPass = DepthPass(width, height, None, draw_scene)
	perspDepthPass = DepthPass(width, height, None, draw_scene)

	with window:
		orthoDepthPass.setup()
		perspDepthPass.setup()

	with window:
		while not window.should_close():
			orthoDepthPass.camera = PerspectiveCamera(glm.inverse(window.view_matrix), glm.radians(60), width/height, 1, 10)
			orthoDepthPass.render()

			perspDepthPass.camera = OrthographicCamera(glm.inverse(window.view_matrix), 5,5, 0.1, 10)
			perspDepthPass.render()

			glClearColor(0,0,0,1)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glDisable(GL_DEPTH_TEST)
			imdraw.texture(perspDepthPass.texture, (0,0,width, height), shuffle=(0,0,0,-1))
			imdraw.texture(orthoDepthPass.texture, (width,0,width, height), shuffle=(0,0,0,-1))

			window.swap_buffers()
			GLFWViewer.poll_events()