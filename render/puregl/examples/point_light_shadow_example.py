from OpenGL.GL import *
import numpy as np
import glm

from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program, fbo
from editor.render import glsl


lightPos = glm.vec3(-2,3,3)
farPlane = 10.0

width, height = 1024, 768
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

with window:
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_CULL_FACE)

	lambert_program = program.create(
		"""
		#version 330 core
		uniform mat4 projectionMatrix;
		uniform mat4 viewMatrix;
		uniform mat4 modelMatrix;
		uniform float farPlane;

		layout (location = 0) in vec3 position;
		layout (location = 2) in vec3 normal;

		out vec3 Normal;
		out vec3 FragPos;

		void main(){
			Normal = normal;
			FragPos = (modelMatrix * vec4(position, 1.0)).xyz;
			gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1.0);
		}
		""",

		"""
		#version 330 core

		in vec3 FragPos;
		in vec3 Normal;
		uniform vec3 lightPos;
		uniform float farPlane;
		out vec4 FragColor;

		uniform samplerCube depthShadowCubemap;

		float PointShadowCalculation(vec3 surfacePos){
			vec3 L = surfacePos-lightPos;
			float closestDepth = texture(depthShadowCubemap, L).r;
			closestDepth*farPlane;

			float currentDepth = length(L);

			float bias = 0.05; 
    		float shadow = currentDepth -  bias > closestDepth ? 1.0 : 0.0;

    		return shadow;
		}

		void main(){
			vec3 N = normalize(Normal);
			vec3 L = normalize(lightPos-FragPos);
			float luminance = max(dot(L, N), 0.0);
			float shadow = PointShadowCalculation(FragPos);
			luminance*=1-shadow;
			vec3 color = vec3(luminance);
			FragColor = vec4(color,1);
		}
		"""
	)

	# create shadow cubemap
	shadow_depth_cubemap = glGenTextures(1)
	shadow_width, shadow_height = 512, 512

	glBindTexture(GL_TEXTURE_CUBE_MAP, shadow_depth_cubemap)

	for i in range(6):
		glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, 0, GL_DEPTH_COMPONENT,
			shadow_width, shadow_height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)

	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

	shadow_depth_fbo = glGenFramebuffers(1)
	glBindFramebuffer(GL_FRAMEBUFFER, shadow_depth_fbo);
	glFramebufferTexture(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, shadow_depth_cubemap, 0)
	glDrawBuffer(GL_NONE)
	glReadBuffer(GL_NONE)

	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	point_shadow_program = program.create(*glsl.read("point_shadow"))

	aspect = shadow_width/shadow_height
	near = 1.0
	far = 25.0
	shadowProj = glm.perspective(glm.radians(90.0), aspect, near, far);

	shadowTransforms = []
	shadowTransforms.append(shadowProj * 
	                 glm.lookAt(lightPos, lightPos + glm.vec3( 1.0, 0.0, 0.0), glm.vec3(0.0,-1.0, 0.0)))
	shadowTransforms.append(shadowProj * 
	                 glm.lookAt(lightPos, lightPos + glm.vec3(-1.0, 0.0, 0.0), glm.vec3(0.0,-1.0, 0.0)))
	shadowTransforms.append(shadowProj * 
	                 glm.lookAt(lightPos, lightPos + glm.vec3( 0.0, 1.0, 0.0), glm.vec3(0.0, 0.0, 1.0)))
	shadowTransforms.append(shadowProj * 
	                 glm.lookAt(lightPos, lightPos + glm.vec3( 0.0,-1.0, 0.0), glm.vec3(0.0, 0.0,-1.0)))
	shadowTransforms.append(shadowProj * 
	                 glm.lookAt(lightPos, lightPos + glm.vec3( 0.0, 0.0, 1.0), glm.vec3(0.0,-1.0, 0.0)))
	shadowTransforms.append(shadowProj * 
	                 glm.lookAt(lightPos, lightPos + glm.vec3( 0.0, 0.0,-1.0), glm.vec3(0.0,-1.0, 0.0)))

	shadowTransforms = np.array([np.array(m) for m in shadowTransforms])

with window:
	while not window.should_close():
		# shadow depth cubemap pass
		with fbo.bind(shadow_depth_fbo), program.use(point_shadow_program) as prog:
			glClear(GL_DEPTH_BUFFER_BIT)
			program.set_uniform(prog, 'farPlane', farPlane)
			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (0,0.5, 0)))
			imdraw.cube(prog)

			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (0,0.0, 0)))
			imdraw.plane(prog)

		# final pass
		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		with program.use(lambert_program) as prog:
			program.set_uniform(prog, 'projectionMatrix', window.projection_matrix)
			glUniformMatrix4fv(glGetUniformLocation(prog, "shadowMatrices"), 6, False, shadowTransforms)
			program.set_uniform(prog, 'viewMatrix', window.view_matrix)
			program.set_uniform(prog, 'farPlane', farPlane)
			

			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_CUBE_MAP, shadow_depth_cubemap)
			program.set_uniform(prog, 'depthShadowCubemap', 0)

			# draw scene
			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (0,0.5, 0)))
			imdraw.cube(prog)

			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (0,0.0, 0)))
			imdraw.plane(prog)

		imdraw.cubemap(shadow_depth_cubemap, window.projection_matrix,  window.view_matrix)

		window.swap_buffers()
		GLFWViewer.poll_events()