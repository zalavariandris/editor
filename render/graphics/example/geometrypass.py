
from OpenGL.GL import *
import numpy as np
from editor.render.puregl import program, texture, fbo
from editor.render import glsl
from renderpass import RenderPass

class GeometryPass(RenderPass):
	def __init__(self, width, height, draw_scene):
		super().__init__(width, height, depth_test=True, cull_face=GL_BACK)
		self.draw_scene = draw_scene

	def setup(self):
		self.geometry_program = program.create(*glsl.read("deferred_geometry"))
		self.gPosition, self.gNormal, self.gAlbedoSpecular = glGenTextures(3)
		self.gBuffer = glGenFramebuffers(1)

		glBindFramebuffer(GL_FRAMEBUFFER, self.gBuffer)
		glDrawBuffers(3, [GL_COLOR_ATTACHMENT0+0, GL_COLOR_ATTACHMENT0+1, GL_COLOR_ATTACHMENT0+2])
		for i, tex in enumerate([self.gPosition, self.gNormal, self.gAlbedoSpecular]):
			glBindTexture(GL_TEXTURE_2D, tex)
			glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
			glFramebufferTexture2D(
				GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0+i, GL_TEXTURE_2D, tex, 0
			)
			glBindTexture(GL_TEXTURE_2D, 0)

		# create depth+stencil buffertarget, pname, param
		rbo = glGenRenderbuffers(1)
		glBindRenderbuffer(GL_RENDERBUFFER, rbo)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
		glBindRenderbuffer(GL_RENDERBUFFER, 0)

		glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
		assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
		glBindFramebuffer(GL_FRAMEBUFFER, 0)

	def resize(self, width, height):
		pass

	def draw(self):
		super().draw()

		with fbo.bind(self.gBuffer), program.use(self.geometry_program) as prog:
			glViewport(0,0, self.width, self.height)
			glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			
			program.set_uniform(prog, "projection", self.camera.projection)
			program.set_uniform(prog, "view", self.camera.view)

			self.draw_scene(prog)

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

	width = 1024
	height = 768
	window = GLFWViewer(width, height, (0.2, 0.2, 0.2, 1.0))
	gPass = GeometryPass(width, height, draw_scene)


	with window:
		gPass.setup()

	with window:
		while not window.should_close():
			camera = PerspectiveCamera(glm.inverse(window.view_matrix), glm.radians(90), width/height, 0.1, 30)
			gPass.camera = camera
			gPass.draw()

			glClearColor(0,0,0,1)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glDisable(GL_DEPTH_TEST)
			imdraw.texture(gPass.gPosition, (0,0,width, height))

			imdraw.texture(gPass.gNormal, (0,0,90, 90))
			imdraw.texture(gPass.gAlbedoSpecular, (100,0,90, 90), shuffle=(0,1,2,-1))
			imdraw.texture(gPass.gAlbedoSpecular, (200,0,90, 90), shuffle=(3,3,3,-1))

			window.swap_buffers()
			GLFWViewer.poll_events()


