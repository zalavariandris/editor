from OpenGL.GL import *
import glm
import numpy as np
from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program, texture, fbo
from editor.render import glsl
from editor.render import assets

import logging
logging.basicConfig(filename=None, level=logging.DEBUG, format='%(levelname)s:%(module)s.%(funcName)s: %(message)s')

from lights import DirectionalLight, Spotlight, Pointlight

def draw_scene(prog, projection, view):
	program.set_uniform(prog, "projection", projection)
	program.set_uniform(prog, "view", view)

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

class GeometryPass:
	def __init__(self):
		self.width, self.height = width, height
		self.gBuffer
		self.geometry_program

		# out
		self.gPosition
		self.gNormal
		self.gAlbedoSpecular

	def __setup__(self):
		pass

	def resize(self, width, height):
		pass

	def __draw__(self):
		pass


class Viewer:
	def __init__(self):
		self.width = 1024
		self.height = 768
		self.window = GLFWViewer(self.width, self.height, (0.2, 0.2, 0.2, 1.0))

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

	def setup(self):
		with self.window:
			glEnable(GL_DEPTH_TEST)
			glEnable(GL_CULL_FACE)
			glEnable(GL_PROGRAM_POINT_SIZE)

			# Geometry Pass
			# -------------
			width, height = self.window.width, self.window.height
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

			self.gBuffer = gBuffer
			self.geometry_program = geometry_program
			self.gPosition, self.gNormal, self.gAlbedoSpecular = gPosition, gNormal, gAlbedoSpecular

	def resize(self):
		with self.window:
			pass


	def draw(self):
		GLFWViewer.poll_events()
		with self.window as window:
			# Geometry Pass
			# -------------
			glCullFace(GL_BACK)
			glEnable(GL_DEPTH_TEST)
			gBuffer = self.gBuffer
			geometry_program = self.geometry_program
			gPosition, gNormal, gAlbedoSpecular = self.gPosition, self.gNormal, self.gAlbedoSpecular

			with fbo.bind(gBuffer), program.use(geometry_program) as prog:
				glViewport(0,0, window.width, window.height)
				glClearColor(0,0,0,0)
				glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
					
				draw_scene(prog, window.projection_matrix, window.view_matrix)

			
			glViewport(0,0, window.width, window.height)
			glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glDisable(GL_DEPTH_TEST)

			# draw to screen
			imdraw.texture(gPosition, (0,0,self.window.width, self.window.height))

			# debug
			imdraw.texture(gNormal, (0,0, 90, 90))
			imdraw.texture(gAlbedoSpecular, (100, 0, 90, 90), shuffle=(0,1,2,-1))
			imdraw.texture(gAlbedoSpecular, (200, 0, 90, 90), shuffle=(3,3,3,-1))

			# swap buffers
			window.swap_buffers()
		


	def start(self):
		self.setup()
		
		while not self.window.should_close():
			self.draw()

if __name__ == "__main__":
	viewer = Viewer()
	viewer.start()

