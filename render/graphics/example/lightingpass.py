from OpenGL.GL import *
import numpy as np
from editor.render import glsl
from editor.render.puregl import imdraw, program, texture, fbo
from renderpass import RenderPass
from editor.render.graphics.lights import DirectionalLight, Spotlight, Pointlight

class LightingPass(RenderPass):
	def __init__(self, width, height, lights):
		super().__init__(width, height, depth_test=False, cull_face=GL_BACK)

		self.lights = lights

		# in
		self.cameraPos = None
		self.gPosition = None
		self.gNormal = None
		self.gAlbedoSpecular = None
		self.irradiance = None
		self.prefilter = None
		self.brdf = None
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

	def render(self):
		assert self.gPosition is not None
		assert self.gNormal is not None
		assert self.gAlbedoSpecular is not None
		assert self.gRoughness is not None
		assert self.gMetallic is not None
		assert self.gEmissive is not None
		assert self.irradiance is not None
		assert self.prefilter is not None
		assert self.brdf is not None
		assert self.cameraPos is not None
		super().render()

		with fbo.bind(self.fbo), program.use(self.prog):
			# clear fbo
			glViewport(0,0, self.width, self.height)
			glClearColor(0.3,0.3,0.3,1.0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

			# configure shader
			program.set_uniform(self.prog, "cameraPos", self.cameraPos)
			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_2D, self.gPosition)
			program.set_uniform(self.prog, "gPosition", 0)

			glActiveTexture(GL_TEXTURE0+1)
			glBindTexture(GL_TEXTURE_2D, self.gNormal)
			program.set_uniform(self.prog, "gNormal", 1)

			glActiveTexture(GL_TEXTURE0+2)
			glBindTexture(GL_TEXTURE_2D, self.gAlbedoSpecular)
			program.set_uniform(self.prog, "gAlbedoSpecular", 2)

			glActiveTexture(GL_TEXTURE0+3)
			glBindTexture(GL_TEXTURE_2D, self.gRoughness)
			program.set_uniform(self.prog, "gRoughness", 2)

			glActiveTexture(GL_TEXTURE0+4)
			glBindTexture(GL_TEXTURE_2D, self.gMetallic)
			program.set_uniform(self.prog, "gMetallic", 2)

			glActiveTexture(GL_TEXTURE0+5)
			glBindTexture(GL_TEXTURE_2D, self.gEmissive)
			program.set_uniform(self.prog, "gEmissive", 2)

			glActiveTexture(GL_TEXTURE0+6)
			glBindTexture(GL_TEXTURE_CUBE_MAP, self.irradiance)
			program.set_uniform(self.prog, "irradianceMap", 3)

			glActiveTexture(GL_TEXTURE0+7)
			glBindTexture(GL_TEXTURE_CUBE_MAP, self.prefilter)
			program.set_uniform(self.prog, "prefilterMap", 4)

			glActiveTexture(GL_TEXTURE0+8)
			glBindTexture(GL_TEXTURE_2D, self.brdf)
			program.set_uniform(self.prog, "brdfLUT", 5)


			shadowMapIdx, shadowCubeIdx = 0, 0
			for i, light in enumerate(self.lights):
				shadow = light.shadowpass
				slot = 9+i
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
