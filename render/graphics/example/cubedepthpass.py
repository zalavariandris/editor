from OpenGL.GL import *
import numpy as np
from editor.render.puregl import program, texture, fbo
from editor.render import glsl
from editor.render import assets
from renderpass import RenderPass
import glm

class CubeDepthPass(RenderPass):
	def __init__(self, width, height, cull_face, near, far, draw_scene):
		super().__init__( width, height, True, cull_face)
		self.near = near
		self.far = far
		self.draw_scene = draw_scene

	@property
	def projection(self):
		aspect = 1.0
		return glm.perspective(glm.radians(90.0), aspect, self.near, self.far)

	@property
	def views(self):
		views = []
		views.append(glm.lookAt(self.position, self.position + glm.vec3( 1, 0, 0), glm.vec3(0,-1, 0)))
		views.append(glm.lookAt(self.position, self.position + glm.vec3(-1, 0, 0), glm.vec3(0,-1, 0)))
		views.append(glm.lookAt(self.position, self.position + glm.vec3( 0, 1, 0), glm.vec3(0, 0, 1)))
		views.append(glm.lookAt(self.position, self.position + glm.vec3( 0,-1, 0), glm.vec3(0, 0,-1)))
		views.append(glm.lookAt(self.position, self.position + glm.vec3( 0, 0, 1), glm.vec3(0,-1, 0)))
		views.append(glm.lookAt(self.position, self.position + glm.vec3( 0, 0,-1), glm.vec3(0,-1, 0)))

		views = np.array([np.array(m) for m in views])
		return views
	
	def setup(self):
		# create program
		# --------------
		self.prog = program.create(*glsl.read("point_shadow"))

		# create depth cubemap texture
		# ----------------------------
		self.cubemap = glGenTextures(1)
		glActiveTexture(GL_TEXTURE0+6+2)
		glBindTexture(GL_TEXTURE_CUBE_MAP, self.cubemap)

		for i in range(6):
			glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, 0, GL_DEPTH_COMPONENT,
				self.width, self.height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)

		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
		
		# create fbo
		self.fbo = glGenFramebuffers(1)
		with fbo.bind(self.fbo):
			glFramebufferTexture(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, self.cubemap, 0)
			glDrawBuffer(GL_NONE)
			glReadBuffer(GL_NONE)
			assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	def draw(self):
		super().draw()

		with fbo.bind(self.fbo), program.use(self.prog):
			# set viewpot
			glViewport(0,0,self.width, self.height)

			# clear fbo
			# glClearColor(0,0,0,1)
			glClear(GL_DEPTH_BUFFER_BIT)

			# configure shader
			for i in range(6):
				program.set_uniform(self.prog, "shadowMatrices[{}]".format(i), self.projection*self.views[i])
			program.set_uniform(self.prog, 'farPlane', float(self.far))
			program.set_uniform(self.prog, 'lightPos', self.position)

			# draw scene
			self.draw_scene(self.prog)


if __name__ == "__main__":
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
	cube_depthpass = CubeDepthPass(512, 512, GL_FRONT, 1.0,30.0, draw_scene)

	with window:
		cube_depthpass.setup()

	with window:
		while not window.should_close():
			cube_depthpass.position = glm.vec3(0,3,0)
			cube_depthpass.draw()

			glClearColor(0.3,0.3,0.3,1)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glDisable(GL_DEPTH_TEST)

			glEnable(GL_DEPTH_TEST)
			imdraw.cubemap(cube_depthpass.cubemap, (0,0,width, height), window.projection_matrix, window.view_matrix)

			window.swap_buffers()
			GLFWViewer.poll_events()


