from OpenGL.GL import *
import numpy as np
import glm

from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program, fbo
from editor.render import glsl

width, height = 1024, 768
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

import logging
logging.basicConfig(filename=None, level=logging.DEBUG, format='%(levelname)s:%(module)s.%(funcName)s: %(message)s')

with window:
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_CULL_FACE)

	# Render lambert pass
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
			float closestDepth = texture(depthShadowCubemap, normalize(L)).r;
			closestDepth*=farPlane;

			float currentDepth = length(L);

			float bias = 0.1; 
    		float shadow = currentDepth -  bias > closestDepth ? 1.0 : 0.0;

    		return shadow;
		}

		void main(){
			// calc simple lambert shading
			vec3 N = normalize(Normal);
			vec3 L = normalize(lightPos-FragPos);
			float distance = length(lightPos-FragPos);
			float luminance = 10*max(dot(L, N), 0.0) / (distance*distance);

			// apply shadow
			float shadow = PointShadowCalculation(FragPos);
			luminance*=1-shadow;

			// create surface color
			vec3 color = vec3(luminance);

			// gamma correction
			const float gamma = 2.2;
    		color = pow(color, vec3(1.0 / gamma));  

			// output surface color
			FragColor = vec4(color, 1.0);
		}
		"""
	)

	# Point Shadow Pass
	# -----------------
	shadow_width, shadow_height = 512, 512
	shadow_depth_fbo = glGenFramebuffers(1)

	# create depth cubemap texture
	shadow_depth_cubemap = glGenTextures(1)
	glBindTexture(GL_TEXTURE_CUBE_MAP, shadow_depth_cubemap)

	for i in range(6):
		glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, 0, GL_DEPTH_COMPONENT,
			shadow_width, shadow_height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)

	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

	# attach cubemap to fbo depth attachment
	glBindFramebuffer(GL_FRAMEBUFFER, shadow_depth_fbo);
	glFramebufferTexture(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, shadow_depth_cubemap, 0)
	glDrawBuffer(GL_NONE)
	glReadBuffer(GL_NONE)
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	# create shader
	point_shadow_program = program.create(*glsl.read("point_shadow"))

	aspect = shadow_width/shadow_height
	near_plane = 1.0
	far_plane = 8.0
	lightPos = glm.vec3(0,3,0)
	
	shadowProj = glm.perspective(glm.radians(90.0), aspect, near_plane, far_plane);

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

import time
with window:
	while not window.should_close():
		# Animate
		# -------
		lightPos = glm.vec3(glm.sin(time.time()*1.6)*2, 3, glm.cos(time.time()*1.6)*2)
		
		# shadow depth cubemap pass
		# -------------------------
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
		glViewport(0, 0, shadow_width, shadow_height);
		with fbo.bind(shadow_depth_fbo), program.use(point_shadow_program) as prog:
			glClear(GL_DEPTH_BUFFER_BIT)
			for i in range(6):
				program.set_uniform(prog, "shadowMatrices[{}]".format(i), shadowTransforms[i])
			program.set_uniform(prog, 'farPlane', far_plane)
			program.set_uniform(prog, 'lightPos', lightPos)

			# draw scene
			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (-1,0.5, -1)))
			imdraw.cube(prog)
			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (1,0.5, -1)))
			imdraw.cube(prog)
			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (1,0.5, 1)))
			imdraw.cube(prog)
			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (-1,0.5, 1)))
			imdraw.cube(prog)

			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (0,0.0, 0)))
			imdraw.plane(prog)

		# Render lambert pass
		# -------------------
		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		with program.use(lambert_program) as prog:
			program.set_uniform(prog, 'projectionMatrix', window.projection_matrix)

			program.set_uniform(prog, 'viewMatrix', window.view_matrix)
			program.set_uniform(prog, 'farPlane', far_plane)
			program.set_uniform(prog, 'lightPos', lightPos)
			
			glActiveTexture(GL_TEXTURE0+1)
			glBindTexture(GL_TEXTURE_CUBE_MAP, shadow_depth_cubemap)
			program.set_uniform(prog, 'depthShadowCubemap', 1)

			# draw scene
			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (-1,0.5, -1)))
			imdraw.cube(prog)
			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (1,0.5, -1)))
			imdraw.cube(prog)
			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (1,0.5, 1)))
			imdraw.cube(prog)
			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (-1,0.5, 1)))
			imdraw.cube(prog)

			program.set_uniform(prog, 'modelMatrix', glm.translate(glm.mat4(1), (0,0.0, 0)))
			imdraw.plane(prog)

		window.swap_buffers()
		GLFWViewer.poll_events()