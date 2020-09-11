from OpenGL.GL import *
import glm
import numpy as np
from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program, texture, fbo
from editor.render import glsl
from editor.render import assets
from editor.render.graphics.cameras import PerspectiveCamera, OrthographicCamera
from renderpass import RenderPass

import logging
logging.basicConfig(filename=None, level=logging.DEBUG, format='%(levelname)s:%(module)s.%(funcName)s: %(message)s')

from editor.render.graphics.lights import DirectionalLight, Spotlight, Pointlight

dirlight = DirectionalLight(direction=glm.vec3(5,-8,-3),
	                        color=glm.vec3(1.0)*1.0,
	                        position=glm.vec3(-5, 8, 3),
	                        radius=5.0,
	                        near=1.0,
	                        far=30)

spotlight = Spotlight(position=glm.vec3(-2, 5.1, -10),
	                  direction=glm.vec3(2, -5.1, 10),
	                  color=glm.vec3(0.2, 0.18, 0.7)*150,
	                  fov=30.0,
	                  near=1.0,
	                  far=30.0)

pointlight = Pointlight(position=glm.vec3(5, 2, 4),
	                    color=glm.vec3(1, 0.7, 0.1)*10,
	                    near=1.0,
	                    far=8.0)

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

from geometrypass import GeometryPass
from depthpass import DepthPass
from cubedepthpass import CubeDepthPass
from environmentpass import EnvironmentPass

class LightingPass(RenderPass):
	def __init__(self, width, height, lights):
		super().__init__(width, height, depth_test=False, cull_face=GL_BACK)

		self.lights = lights

		# in
		self.gPosition = None
		self.gNormal = None
		# out
		self.beauty=None

	def setup(self):
		# create program
		# --------------
		self.prog = program.create(*glsl.read("PBR2"))

		with program.use(self.prog):
			program.set_uniform(self.prog, "projectionMatrix", np.eye(4))
			program.set_uniform(self.prog, "viewMatrix", np.eye(4))
			program.set_uniform(self.prog, "modelMatrix", np.eye(4))

		# create textures
		# ---------------
		self.beauty = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.beauty)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glBindTexture(GL_TEXTURE_2D, 0)

		# create fbo
		# ----------
		self.fbo = glGenFramebuffers(1)
		glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
		glDrawBuffers(1, [GL_COLOR_ATTACHMENT0+0])
		glBindTexture(GL_TEXTURE_2D, self.beauty)
		glFramebufferTexture2D(
			GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0+0, GL_TEXTURE_2D, self.beauty, 0
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

	def draw(self):
		assert self.gPosition is not None
		assert self.gNormal is not None
		super().draw()

		with fbo.bind(self.fbo), program.use(self.prog):
			# clear fbo
			glViewport(0,0, self.width, self.height)
			glClearColor(0.3,0.3,0.3,1.0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

			# configure shader
			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_2D, self.gPosition)
			glActiveTexture(GL_TEXTURE0+1)
			glBindTexture(GL_TEXTURE_2D, self.gNormal)
			program.set_uniform(self.prog, "gPosition", 0)
			program.set_uniform(self.prog, "gNormal", 1)

			shadowMapIdx, shadowCubeIdx = 0, 0
			for i, light in enumerate(self.lights):
				shadow = light.shadowpass
				slot = 2+i
				if isinstance(light, DirectionalLight):
					program.set_uniform(self.prog, "lights[{}].type".format(i), 0)
					program.set_uniform(self.prog, "lights[{}].color".format(i), light.color)

					program.set_uniform(self.prog, "lights[{}].direction".format(i), light.direction)
					program.set_uniform(self.prog, "lights[{}].shadowIdx".format(i), shadowMapIdx)
					
					glActiveTexture(GL_TEXTURE0+slot)
					glBindTexture(GL_TEXTURE_2D, shadow.texture)
					program.set_uniform(self.prog, "lights[{}].matrix".format(i), light.camera.projection * light.camera.view)
					program.set_uniform(self.prog, "shadowMaps[{}]".format(shadowMapIdx), slot)
					shadowMapIdx+=1

				elif isinstance(light, Spotlight):
					program.set_uniform(self.prog, "lights[{}].type".format(i), 1)
					program.set_uniform(self.prog, "lights[{}].color".format(i), light.color)

					program.set_uniform(self.prog, "lights[{}].position".format(i), light.position)
					program.set_uniform(self.prog, "lights[{}].direction".format(i), light.direction)
					program.set_uniform(self.prog, "lights[{}].cutOff".format(i), light.cut_off)

					glActiveTexture(GL_TEXTURE0+slot)
					glBindTexture(GL_TEXTURE_2D, shadow.texture)
					program.set_uniform(self.prog, "lights[{}].matrix".format(i), light.camera.projection * light.camera.view)
					program.set_uniform(self.prog, "lights[{}].shadowIdx".format(i), shadowMapIdx)
					program.set_uniform(self.prog, "shadowMaps[{}]".format(shadowMapIdx), slot)
					shadowMapIdx+=1

				elif isinstance(light, Pointlight):
					program.set_uniform(self.prog, "lights[{}].type".format(i), 2)
					program.set_uniform(self.prog, "lights[{}].color".format(i), light.color)

					program.set_uniform(self.prog, "lights[{}].position".format(i), light.position)

					glActiveTexture(GL_TEXTURE0+slot)
					glBindTexture(GL_TEXTURE_CUBE_MAP, shadow.cubemap)
					program.set_uniform(self.prog, "lights[{}].farPlane".format(i), float(shadow.far))
					program.set_uniform(self.prog, "lights[{}].shadowIdx".format(i), shadowCubeIdx)
					program.set_uniform(self.prog, "shadowCubes[{}]".format(shadowCubeIdx), slot)
					shadowCubeIdx+=1
			# draw
			imdraw.quad(self.prog)


class Viewer:
	def __init__(self):
		self.width = 1024
		self.height = 768
		self.window = GLFWViewer(self.width, self.height, (0.2, 0.2, 0.2, 1.0))

		self.camera = PerspectiveCamera(glm.inverse(self.window.view_matrix), glm.radians(60), self.width/self.height, 1, 30)

		self.geometry_pass = GeometryPass(self.width, self.height, draw_scene)

		self.lighting_pass = LightingPass(self.width, self.height, lights=[dirlight, spotlight, pointlight])

		dirlight.shadowpass = DepthPass(1024, 1024, GL_FRONT, draw_scene,)
		spotlight.shadowpass = DepthPass(1024, 1024, GL_FRONT, draw_scene)
		pointlight.shadowpass = CubeDepthPass(512, 512, GL_FRONT, near=1, far=15, draw_scene=draw_scene)

		
		self.environment_image = assets.imread('hdri/Tropical_Beach_3k.hdr')
		self.environment_pass = EnvironmentPass(512,512)

	def setup(self):	
		glEnable(GL_PROGRAM_POINT_SIZE)

		# Geometry Pass
		# -------------
		self.geometry_pass.setup()
		dirlight.shadowpass.setup()
		pointlight.shadowpass.setup()
		spotlight.shadowpass.setup()
		# create environment texture
		w, h, c = self.environment_image.shape
		self.environment_tex = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.environment_tex)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, w, h, 0, GL_RGB, GL_FLOAT, self.environment_image)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glBindTexture(GL_TEXTURE_2D, 0)
		self.environment_pass.texture = self.environment_tex
		self.environment_pass.setup()
		self.environment_pass.draw()
		self.lighting_pass.setup()

	def resize(self):
		with self.window:
			pass

	def draw(self):
		# Animate
		# -------
		import math, time
		spotlight.position = glm.vec3(math.cos(time.time()*3)*4, 0.3, -4)
		spotlight.direction = -spotlight.position
		pointlight.position = glm.vec3(math.cos(time.time())*4, 4, math.sin(time.time())*4)
		self.camera.transform = glm.inverse(self.window.view_matrix)

		# Render passes
		# -------------
		## Geometry
		self.geometry_pass.camera = self.camera #window.projection_matrix, window.view_matrix
		self.geometry_pass.draw()

		## Shadowmaps
		dirlight.shadowpass.camera = dirlight.camera
		dirlight.shadowpass.draw()
		spotlight.shadowpass.camera = spotlight.camera
		spotlight.shadowpass.draw()
		pointlight.shadowpass.position = pointlight.position
		pointlight.shadowpass.draw()

		## Lighting
		self.lighting_pass.gPosition = self.geometry_pass.gPosition
		self.lighting_pass.gNormal = self.geometry_pass.gNormal

		self.lighting_pass.draw()

		# Render to screen
		# ----------------			
		glViewport(0,0, self.width, self.height)
		glClearColor(0.5,0.5,0.5,1)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glDisable(GL_DEPTH_TEST)

		# draw to screen
		imdraw.texture(self.lighting_pass.beauty, (0, 0, self.width, self.height))

		# debug
		imdraw.texture(self.geometry_pass.gPosition,       (  0,   0, 90, 90))
		imdraw.texture(self.geometry_pass.gNormal,         (100,   0, 90, 90))
		imdraw.texture(self.geometry_pass.gAlbedoSpecular, (200,   0, 90, 90), shuffle=(0,1,2,-1))
		imdraw.texture(self.geometry_pass.gAlbedoSpecular, (300,   0, 90, 90), shuffle=(3,3,3,-1))

		imdraw.texture(dirlight.shadowpass.texture, (0, 100, 90, 90), shuffle=(0,0,0,-1))
		imdraw.texture(spotlight.shadowpass.texture, (100, 100, 90, 90), shuffle=(0,0,0,-1))
		imdraw.cubemap(pointlight.shadowpass.cubemap, (200, 100, 90, 90), self.window.projection_matrix, self.window.view_matrix)


		imdraw.texture(self.environment_tex, (0, 200, 90,90))
		imdraw.cubemap(self.environment_pass.cubemap, (100, 200, 90, 90), self.window.projection_matrix, self.window.view_matrix)
		# swap buffers
		# ------------
		self.window.swap_buffers()
		GLFWViewer.poll_events()
		
	def start(self):
		with self.window:
			self.setup()
			while not self.window.should_close():
				self.draw()


if __name__ == "__main__":
	viewer = Viewer()
	viewer.start()

