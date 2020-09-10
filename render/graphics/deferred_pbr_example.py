from OpenGL.GL import *
import glm
import numpy as np
from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program, texture, fbo
from editor.render import glsl
from editor.render import assets
from cameras import PerspectiveCamera, OrthographicCamera

import logging
logging.basicConfig(filename=None, level=logging.DEBUG, format='%(levelname)s:%(module)s.%(funcName)s: %(message)s')

from lights import DirectionalLight, Spotlight, Pointlight

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
	                  near=0.1,
	                  far=13.0)

pointlight = Pointlight(position=glm.vec3(5, 2, 0.5),
	                    color=glm.vec3(1, 0.7, 0.1)*30,
	                    near=1.0,
	                    far=8.0)

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
	def __init__(self, width, height, depth_test, cull_face):
		# properties
		self.width, self.height = width, height
		self.depth_test = depth_test
		self.cull_face = cull_face

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
		if self.cull_face:
			glEnable(GL_CULL_FACE)
			glCullFace(self.cull_face)
		else:
			glDisable(GL_CULL_FACE)
		if self.depth_test:
			glEnable(GL_DEPTH_TEST)
		else:
			glDisable(GL_DEPTH_TEST)

		with fbo.bind(self.gBuffer), program.use(self.geometry_program) as prog:
			glViewport(0,0, self.width, self.height)
			glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
				
			draw_scene(prog, self.camera.projection, self.camera.view)


class LightingPass:
	def __init__(self, width, height, depth_test, cull_face, lights):
		# properties
		self.width, self.height = width, height
		self.depth_test = depth_test
		self.cull_face = cull_face

		self.lights = lights

	def setup(self):
		# create program
		# --------------
		self.prog = program.create(
			"""
			#version 330 core
			layout (location=0) in vec3 position;
			layout (location=1) in vec2 uv;
			uniform mat4 projectionMatrix;
			uniform mat4 viewMatrix;
			uniform mat4 modelMatrix;

			out vec2 TexCoords;

			void main(){
				TexCoords = uv;
				gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1.0);
			}
			""",
			"""
			#version 330 core
			#define NUM_LIGHTS 3
			#define NUM_SHADOWMAPS 2
			#define NUM_SHADOWCUBES 1

			uniform sampler2D gPosition;
			uniform sampler2D gNormal;
			in vec2 TexCoords;
			out vec4 FragColor;

			struct Light{
				int type;
				vec3 color;
				vec3 position;
				vec3 direction;
				float cutOff;
				mat4 matrix;
				int shadowIdx;

				float nearPlane;
				float farPlane;
			};

			uniform Light lights[NUM_LIGHTS];
			uniform sampler2D shadowMaps[NUM_SHADOWMAPS];
			uniform samplerCube shadowCubes[NUM_SHADOWCUBES];

			float ShadowCalculation(vec4 fragPosLightSpace, vec3 lightDir, vec3 normal, sampler2D shadowMap){
				// perform perspective divide
				vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;

				projCoords = projCoords*0.5+0.5;
				if(projCoords.z>1.0)
					return 0.0;

				float closestDepth = texture(shadowMap, projCoords.xy).r;
				float currentDepth = projCoords.z;

				if(dot(normal, lightDir)<0.0)
				  return 0.0;

				// float bias = max(0.005 * (1.0 - dot(normal, lightDir)), 0.0005);
				float bias = 0.0001;
				float pcfDepth = texture(shadowMap, projCoords.xy).r; 
				float shadow = currentDepth - bias > pcfDepth ? 1.0 : 0.0;
				return shadow;
			}

			float PointShadowCalculation(vec3 lightPos, vec3 surfacePos, samplerCube shadowCubemap, float farPlane){
				vec3 L=surfacePos-lightPos;
				float shadowDepth = texture(shadowCubemap, normalize(L)).r;
				shadowDepth*=farPlane;

				float surfaceDepth = length(L);

				float bias = 0.1;
				float shadow = surfaceDepth > shadowDepth ? 1.0 : 0.0;

				return shadow;
			}

			void main()
			{
				vec3 surfacePos = texture(gPosition, TexCoords).rgb;
				vec3 surfaceNormal = texture(gNormal, TexCoords).rgb;
				vec3 N = normalize(surfaceNormal);

				// lambert shading
				vec3 Lo=vec3(0);
				for(int i=0; i<NUM_LIGHTS; ++i)
				{
					vec3 L=vec3(0);
					float attenuation=1.0;
					if(lights[i].type==0)
					{
						L = normalize(-lights[i].direction);
						attenuation=1.0;

						// calc shadow
						vec4 fragPosLightSpace = lights[i].matrix * vec4(surfacePos, 1.0);
						float shadow = ShadowCalculation(fragPosLightSpace, L, N, shadowMaps[lights[i].shadowIdx]);
						attenuation*=1-shadow;
					}
					else if(lights[i].type==1)
					{
						L = normalize(lights[i].position - surfacePos);
						float distance = length(lights[i].position - surfacePos);
						attenuation = 1.0 / (distance*distance);

						// spotlight cutoff
						if(lights[i].cutOff>=0)
						{
							float theta = dot(L, normalize(-lights[i].direction));
							if(theta<lights[i].cutOff){
								attenuation=0.0;
							}
						}

						// calc shadow
						vec4 fragPosLightSpace = lights[i].matrix * vec4(surfacePos, 1.0);
						float shadow = ShadowCalculation(fragPosLightSpace, L, N, shadowMaps[lights[i].shadowIdx]);
						attenuation*=1-shadow;
					}
					else if(lights[i].type==2){
						L = normalize(lights[i].position - surfacePos);
						float distance = length(lights[i].position - surfacePos);
						attenuation = 1.0 / (distance*distance);

						// // calc shadow
						//float shadow = PointShadowCalculation(lights[i].position, surfacePos, shadowCubes[0], lights[i].farPlane);
						//attenuation*=1-shadow;
					}

					vec3 radiance = lights[i].color * attenuation;
					


					
					float diff = max(dot(N, L), 0.0);
					Lo+=diff*radiance;
				}
				vec3 color = Lo;

				FragColor = vec4(color, 1.0);
			}
			""")

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
		if self.cull_face:
			glEnable(GL_CULL_FACE)
			glCullFace(self.cull_face)
		else:
			glDisable(GL_CULL_FACE)
		if self.depth_test:
			glEnable(GL_DEPTH_TEST)
		else:
			glDisable(GL_DEPTH_TEST)

		with fbo.bind(self.fbo), program.use(self.prog):
			# clear fbo
			glViewport(0,0, self.width, self.height)
			glClearColor(0.3,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

			# configure shader
			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_2D, self.gPosition)
			glActiveTexture(GL_TEXTURE0+1)
			glBindTexture(GL_TEXTURE_2D, self.gNormal)
			program.set_uniform(self.prog, "gPosition", 0)
			program.set_uniform(self.prog, "gNormal", 1)

			shadowMapIdx, shadowCubeIdx = 0, 0
			for i, (shadowmap, light) in enumerate(zip(self.shadowmaps, self.lights)):
				if isinstance(light, DirectionalLight):
					program.set_uniform(self.prog, "lights[{}].type".format(i), 0)
					program.set_uniform(self.prog, "lights[{}].color".format(i), light.color)

					program.set_uniform(self.prog, "lights[{}].direction".format(i), light.direction)
					program.set_uniform(self.prog, "lights[{}].shadowIdx".format(i), shadowMapIdx)
					

					glActiveTexture(GL_TEXTURE0+2+i)
					glBindTexture(GL_TEXTURE_2D, shadowmap)
					program.set_uniform(self.prog, "lights[{}].matrix".format(i), light.camera.projection * light.camera.view)
					program.set_uniform(self.prog, "shadowMaps[{}]".format(i), 2+i)

					shadowMapIdx+=2

				elif isinstance(light, Spotlight):
					program.set_uniform(self.prog, "lights[{}].type".format(i), 1)
					program.set_uniform(self.prog, "lights[{}].color".format(i), light.color)

					program.set_uniform(self.prog, "lights[{}].position".format(i), light.position)
					program.set_uniform(self.prog, "lights[{}].direction".format(i), light.direction)
					program.set_uniform(self.prog, "lights[{}].shadowIdx".format(i), i)
					program.set_uniform(self.prog, "lights[{}].cutOff".format(i), light.cut_off)

					glActiveTexture(GL_TEXTURE0+2+i)
					glBindTexture(GL_TEXTURE_2D, shadowmap)
					program.set_uniform(self.prog, "lights[{}].matrix".format(i), light.camera.projection * light.camera.view)
					program.set_uniform(self.prog, "shadowMaps[{}]".format(i), 2+i)




			# draw
			imdraw.quad(self.prog)


class DepthPass:
	def __init__(self, width, height, depth_test, cull_face):
		self.width = width
		self.height = height
		self.depth_test = depth_test
		self.cull_face = cull_face

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

	def draw(self):
		if self.cull_face:
			glEnable(GL_CULL_FACE)
			glCullFace(self.cull_face)
		else:
			glDisable(GL_CULL_FACE)
		if self.depth_test:
			glEnable(GL_DEPTH_TEST)
		else:
			glDisable(GL_DEPTH_TEST)

		with fbo.bind(self.fbo), program.use(self.prog):
			# set viewport
			glViewport(0,0, self.width, self.height)

			# clear fbo
			glClear(GL_DEPTH_BUFFER_BIT)

			# configure shaders


			# draw scene
			draw_scene(self.prog, self.camera.projection, self.camera.view)


class EnvironmentPass:
	def __init__(self):
		pass

	def setup(self):
		pass

	def draw(self):
		pass


class Viewer:
	def __init__(self):
		self.width = 1024
		self.height = 768
		self.window = GLFWViewer(self.width, self.height, (0.2, 0.2, 0.2, 1.0))

		self.camera = PerspectiveCamera(glm.inverse(self.window.view_matrix), glm.radians(90), self.width/self.height, 1, 30)

		self.geometry_pass = GeometryPass(
			self.width, self.height,
			depth_test=True,
			cull_face=GL_BACK
		)

		self.lighting_pass = LightingPass(
			self.width, self.height,
			depth_test=False,
			cull_face=GL_BACK,
			lights=[dirlight, spotlight]
		)

		self.shadowpasses = []
		for light in self.lighting_pass.lights:
			self.shadowpasses.append( DepthPass(1024,1024, depth_test=True, cull_face=GL_FRONT) )
		
	def setup(self):
		with self.window:
			
			glEnable(GL_PROGRAM_POINT_SIZE)

			# Geometry Pass
			# -------------
			self.geometry_pass.setup()
			for shadowpass in self.shadowpasses:
				shadowpass.setup()
			self.lighting_pass.setup()

	def resize(self):
		with self.window:
			pass

	def draw(self):
		import math, time
		spotlight.position = glm.vec3(math.cos(time.time()*3)*4, 0.3, -4)
		spotlight.direction = -spotlight.position

		# update camera 
		self.camera.transform = glm.inverse(self.window.view_matrix)

		GLFWViewer.poll_events()
		with self.window as window:
			# Render passes
			# -------------
			self.geometry_pass.camera = self.camera #window.projection_matrix, window.view_matrix
			self.geometry_pass.draw()

			for shadowpass, light in zip(self.shadowpasses, self.lighting_pass.lights):
				shadowpass.camera = light.camera
			for shadowpass in self.shadowpasses:
				shadowpass.draw()

			self.lighting_pass.gPosition = self.geometry_pass.gPosition
			self.lighting_pass.gNormal = self.geometry_pass.gNormal
			self.lighting_pass.shadowmaps = [shadowpass.texture for shadowpass in self.shadowpasses]
			self.lighting_pass.draw()

			# Render to screen
			# ----------------			
			glViewport(0,0, window.width, window.height)
			glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glDisable(GL_DEPTH_TEST)

			# draw to screen
			imdraw.texture(self.lighting_pass.beauty, (0, 0, self.window.width, self.window.height))

			# debug
			imdraw.texture(self.geometry_pass.gPosition,       (  0,   0, 90, 90))
			imdraw.texture(self.geometry_pass.gNormal,         (100,   0, 90, 90))
			imdraw.texture(self.geometry_pass.gAlbedoSpecular, (200,   0, 90, 90), shuffle=(0,1,2,-1))
			imdraw.texture(self.geometry_pass.gAlbedoSpecular, (300,   0, 90, 90), shuffle=(3,3,3,-1))

			for i, shadowpass in enumerate(self.shadowpasses):
				imdraw.texture(shadowpass.texture,       (  i*100, 100, 90, 90), shuffle=(0,0,0,-1))

			# swap buffers
			# ------------
			window.swap_buffers()
		
	def start(self):
		self.setup()
		
		while not self.window.should_close():
			self.draw()


if __name__ == "__main__":
	viewer = Viewer()
	viewer.start()

