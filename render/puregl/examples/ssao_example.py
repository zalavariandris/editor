from OpenGL.GL import *
import numpy as np
import glm

from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program, fbo
from editor.render import glsl


width, height = 1024, 768
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

with window:
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_CULL_FACE)

	ssao_program = program.create(
		"""
		#version 330 core
		uniform mat4 projectionMatrix;
		uniform mat4 viewMatrix;
		uniform mat4 modelMatrix;

		layout (location = 0) in vec3 position;
		layout (location = 1) in vec2 uv;
		layout (location = 2) in vec3 normal;

		out vec2 TexCoords;
		out vec3 FragPos;
		out vec3 Normal;

		void main(){
			
			vec4 viewPos = viewMatrix * modelMatrix * vec4(position, 1.0);
			FragPos = viewPos.xyz;
			TexCoords = uv;

			mat3 normalMatrix = transpose(inverse(mat3(viewMatrix*modelMatrix)));
			Normal = normalMatrix * normal;

			gl_Position = projectionMatrix * viewPos;
		}
		""", 

		"""
		#version 330 core
		uniform vec3 albedo;
		layout (location=0) out vec3 gPosition;
		layout (location=1) out vec3 gNormal;
		layout (location=2) out vec4 gAlbedoSpec;

		in vec2 TexCoords;
		in vec3 FragPos;
		in vec3 Normal;

		void main(){
			gPosition = FragPos;
			gNormal = normalize(Normal);
			gAlbedoSpec.rgb = vec3(0.95);
		}
		"""
	)

	# create gBuffer
	# --------------
	gBuffer = glGenFramebuffers(1)
	ssao_width = window.width
	ssao_height = window.height
	gPosition, gNormal, gAlbedo = glGenTextures(3)

	with fbo.bind(gBuffer):
		# create color attachments
		glDrawBuffers(3, [GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1, GL_COLOR_ATTACHMENT2])
		for i, tex in enumerate([gPosition, gNormal, gAlbedo]):
			glBindTexture(GL_TEXTURE_2D, tex)
			glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, ssao_width, ssao_height, 0, GL_RGB, GL_FLOAT, None)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		
			# attach to color
			glFramebufferTexture2D(
				GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0 + i, GL_TEXTURE_2D, tex, 0
			)
			glBindTexture(GL_TEXTURE_2D, 0)

		# create depth+stencil buffer
		rbo = glGenRenderbuffers(1)
		glBindRenderbuffer(GL_RENDERBUFFER, rbo)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, ssao_width, ssao_height)
		glBindRenderbuffer(GL_RENDERBUFFER, 0)

		glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
		assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
		
	# generate sample kernel
	# ----------------------
	ssaoKernel = []
	for i in range(64):
		sample = glm.vec3(np.random.uniform((-1, -1, 0), (1,1,1), (3, )))
		sample = glm.normalize(sample)
		sample*=np.random.uniform(0,1)
		scale = i/64

		# scale samples s.t. they are more aligned to center of kernel
		scale = glm.mix(0.1, 1.0, scale*scale)
		sample*=scale
		ssaoKernel.append(sample)

	for sample in ssaoKernel:
		program.set_uniform(ssao_program, 'samples[{}]'.format(i), sample)


	while not window.should_close():
		# ssao - geometry pass
		with fbo.bind(gBuffer):
			glViewport(0, 0, window.width, window.height)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			with program.use(ssao_program):
				program.set_uniform(ssao_program, 'projectionMatrix', window.projection_matrix)
				program.set_uniform(ssao_program, 'viewMatrix', window.view_matrix)

				# draw cube
				translation = glm.translate(glm.mat4(1), (0,0.5,0))
				rotation = glm.rotate(glm.mat4(1), 0, (0,1,0))
				scale = glm.scale(glm.mat4(1), (1,1,1))
				program.set_uniform(ssao_program, 'modelMatrix', translation*rotation*scale)
				program.set_uniform(ssao_program, 'albedo', (0.2,0.8,0.8))
				imdraw.cube(ssao_program)

				# draw room
				translation = glm.translate(glm.mat4(1), (0,2.5,0))
				rotation = glm.rotate(glm.mat4(1), 0, (0,1,0))
				scale = glm.scale(glm.mat4(1), (10,5,10))
				program.set_uniform(ssao_program, 'modelMatrix', translation*rotation*scale)
				program.set_uniform(ssao_program, 'albedo', (0.2,0.3,0.4))
				imdraw.cube(ssao_program, flip=True)

		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		imdraw.texture(gPosition, (0,0,window.width, window.height), shuffle=(0, 1, 2, -1))

		window.swap_buffers()
		GLFWViewer.poll_events()