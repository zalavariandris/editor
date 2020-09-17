from OpenGL.GL import *
import numpy as np
from editor.render.puregl import program, texture, fbo
from editor.render import glsl
from editor.render import assets
from renderpass import RenderPass
import glm
from editor.render.puregl import imdraw


class EnvironmentPass(RenderPass):
	"""
	texture->cubemap
	"""
	def __init__(self, width, height):
		super().__init__(width,height, depth_test=False, cull_face=None)

		# in
		self.texture=None

		# out
		self.cubemap=None

	def setup(self):
		# Crate program
		# -------------
		self.prog = program.create(
			"""#version 330 core
			layout (location = 0) in vec3 position;

			out vec3 SurfacePos;

			uniform mat4 projectionMatrix;
			uniform mat4 viewMatrix;

			void main()
			{
			    SurfacePos = position;
			    gl_Position =  projectionMatrix * viewMatrix * vec4(SurfacePos, 1.0);
			}
			""",
			"""
			#version 330 core
			out vec4 FragColor;
			in vec3 SurfacePos;

			uniform sampler2D equirectangularMap;

			const vec2 invAtan = vec2(0.1591, 0.3183);
			vec2 SampleSphericalMap(vec3 v)
			{
			    vec2 uv = vec2(atan(v.z, v.x), asin(-v.y));
			    uv *= invAtan;
			    uv += 0.5;
			    return uv;
			}

			void main()
			{		
			    vec2 uv = SampleSphericalMap(normalize(SurfacePos));
			    vec3 color = texture(equirectangularMap, uv).rgb;
			    
			    FragColor = vec4(color, 1.0);
			}
			""")
	
		# Create textures
		# ---------------
		self.cubemap = glGenTextures(1)
		glBindTexture(GL_TEXTURE_CUBE_MAP, self.cubemap)
		for i in range(6):
			glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, 0, 
				GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
		
		glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

		# setup cubemap projections
		self.projection = glm.perspective(glm.radians(90), 1.0,0.1,10.0)
		self.views = [
			glm.lookAt((0, 0, 0), ( 1,  0,  0), (0, -1,  0)),
			glm.lookAt((0, 0, 0), (-1,  0,  0), (0, -1,  0)),
			glm.lookAt((0, 0, 0), ( 0,  1,  0), (0,  0,  1)),
			glm.lookAt((0, 0, 0), ( 0, -1,  0), (0,  0, -1)),
			glm.lookAt((0, 0, 0), ( 0,  0,  1), (0, -1,  0)),
			glm.lookAt((0, 0, 0), ( 0,  0, -1), (0, -1,  0))
		]

		# create depth+stencil RBO
		rbo = glGenRenderbuffers(1)
		glBindRenderbuffer(GL_RENDERBUFFER, rbo)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height)
		glBindRenderbuffer(GL_RENDERBUFFER, 0)

		# Create fbo
		# ----------
		self.fbo = glGenFramebuffers(1)
		with fbo.bind(self.fbo):
			glFramebufferRenderbuffer(GL_FRAMEBUFFER, 
				GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rbo)

			assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	def render(self):
		assert self.texture is not None
		super().render()
		# set viewport
		glViewport(0,0,self.width, self.height)

		# draw cube
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_2D, self.texture)
		with program.use(self.prog):
			program.set_uniform(self.prog, 'equirectangularMap', 0)
			program.set_uniform(self.prog, "projectionMatrix", self.projection)

			with fbo.bind(self.fbo):
				for i in range(6):
					glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, self.cubemap, 0)	
					program.set_uniform(self.prog, "viewMatrix", self.views[i])
					# glClearColor(0,0,0,1)
					glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
					imdraw.cube(self.prog, flip=True)
		glBindTexture(GL_TEXTURE_2D, 0)


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
	environment_image = assets.imread('hdri/Tropical_Beach_3k.hdr')
	# environment_image = assets.imread('container2_axis.png')[...,:3]/255
	envpass = EnvironmentPass(512, 512)

	with window:
		envtex = texture.create(environment_image, 0, GL_RGB)
		envpass.setup()

	with window:
		while not window.should_close():
			envpass.texture = envtex
			envpass.render()

			glClearColor(0.3,0.3,0.3,1)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glDisable(GL_DEPTH_TEST)
			imdraw.texture(envtex, (0,0,90, 90), shuffle=(0,1,2,-1))
			
			imdraw.cubemap(envpass.cubemap, (0,0,width, height), window.projection_matrix, window.view_matrix)

			window.swap_buffers()
			GLFWViewer.poll_events()


