from editor.render import gloo
from editor.utils import profile
from editor.render.gloo.helpers import box, plane
from editor.render.window import GLFWViewer
from OpenGL.GL import *
import OpenGL

import numpy as np
from pathlib import Path
import glm
import math
from PIL import Image
from editor import utils

from editor.render.gloo.helpers import buffer_offset
from editor.utils import memoize

from pathlib import Path
import imageio

# puregl
import program
import imdraw
import texture
import fbo

from editor.render import glsl

import logging
logging.basicConfig(filename=None, level=logging.DEBUG, format='%(levelname)s:%(module)s.%(funcName)s: %(message)s')

# Init
width, height = 1024, 768
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

#
# read assets
#
assets_folder = "../assets"
def to_srgb(img, gamma=2.2):
	return np.power(img, (1/gamma, 1/gamma, 1/gamma))

def to_linear(img, gamma=2.2):
	return np.power(img, (gamma, gamma, gamma))

# textures
diffuse_data  = np.array(Image.open(Path(assets_folder, 'container2_axis.png')))[...,[2,1,0]]/255
specular_data = np.array(Image.open(Path(assets_folder, 'container2_specular.png')))[...,[2,1,0]]/255
diffuse_data  = to_linear(diffuse_data)
specular_data = to_linear(specular_data)

# environment
environment_data = imageio.imread(Path(assets_folder, 'hdri/fin4_Ref.hdr'), format="HDR-FI")

with window:
	glEnable(GL_PROGRAM_POINT_SIZE)
	glEnable(GL_DEPTH_TEST)
	
	# create material textures
	diffuse_tex = texture.create(diffuse_data, slot=0, format=GL_BGR)
	specular_tex = texture.create(specular_data, slot=1, format=GL_BGR)

	# create programs
	lambert_program = program.create(*glsl.read('lambert'))
	phong_program = program.create(*glsl.read('phong'))
	pbr_program = program.create(*glsl.read('pbr'))

	# setup Shadow mapping
	# ----------------------
	depth_program = program.create(*glsl.read('simple_depth'))
	shadow_fbo = glGenFramebuffers(1)
	shadow_fbo_width, shadow_fbo_height = 1024, 1024
	shadow_tex = texture.create((shadow_fbo_width, shadow_fbo_height), 
				slot=2, 
				format=GL_DEPTH_COMPONENT,
				wrap_s=GL_CLAMP_TO_BORDER,
				wrap_t=GL_CLAMP_TO_BORDER, 
				border_color=(1.0, 1.0, 1.0, 1.0))


	with fbo.bind(shadow_fbo):
		# dont render color data
		glDrawBuffer(GL_NONE) # dont render color data
		glReadBuffer(GL_NONE)
		# attach depth component to texture
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, shadow_tex, 0)

	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE


	
	

	# Setup Tonemapping with HDR fbo
	# ------------------------------
	tonamapping_program = program.create(*glsl.read('tonemapping'))
	
	# setup fbo
	hdr_fbo = glGenFramebuffers(1)
	hdr_fbo_width, hdr_fbo_height = width, height # initalize FBO with window size

	# create HDR color texture
	hdr_tex = glGenTextures(1)
	glActiveTexture(GL_TEXTURE0)
	glBindTexture(GL_TEXTURE_2D, hdr_tex)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, hdr_fbo_width, hdr_fbo_height, 0, GL_RGB, GL_FLOAT, None)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	glBindTexture(GL_TEXTURE_2D, 0)

	# create depth+stencil buffer
	rbo = glGenRenderbuffers(1)
	glBindRenderbuffer(GL_RENDERBUFFER, rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, hdr_fbo_width, hdr_fbo_height)
	glBindRenderbuffer(GL_RENDERBUFFER, 0)

	with fbo.bind(hdr_fbo):
		## attach color component
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, hdr_tex, 0)

		## attach depth and stencil component
		glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
		
		assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
		
	# Environment and IBL
	# -------------------------
	# - capture environment map to cubemap
	equirectangular_to_cubemap_program = program.create(*glsl.read('cubemap.vs', 'equirectangular_to_cubemap.fs'))
	# - setup skybox drawing
	skybox_program = program.create(*glsl.read('skybox'))
	# - create irradiance map for diffuse IBL
	irradiance_program = program.create(*glsl.read('cubemap.vs', 'irradiance_convolution.fs'))
	# - create prefilter map for specular IBL
	prefilterShader = program.create(*glsl.read('cubemap.vs', 'prefilter.fs'))
	# precompute brdf map for specular IBL
	brdfShader = program.create(*glsl.read('brdf'))

	## Prepare Environment map (convert an equirectangular image to cubemap)
	# create environment texture
	env_height, env_width, env_channels = environment_data.shape
	environment_tex = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, environment_tex)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB16F, env_width, env_height, 0, GL_RGB, GL_FLOAT, environment_data)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

	# setup cubemap
	env_cubemap = glGenTextures(1)
	glBindTexture(GL_TEXTURE_CUBE_MAP, env_cubemap)
	for i in range(6):
		glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, 0, GL_RGB16F, 512,512,0,GL_RGB, GL_FLOAT, None)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

	# setup cubemap projections to render each face
	capture_projection = glm.perspective(glm.radians(90), 1.0,0.1,10.0)
	capture_views = [
		glm.lookAt((0, 0, 0), ( 1,  0,  0), (0, -1,  0)),
		glm.lookAt((0, 0, 0), (-1,  0,  0), (0, -1,  0)),
		glm.lookAt((0, 0, 0), ( 0,  1,  0), (0,  0,  1)),
		glm.lookAt((0, 0, 0), ( 0, -1,  0), (0,  0, -1)),
		glm.lookAt((0, 0, 0), ( 0,  0,  1), (0, -1,  0)),
		glm.lookAt((0, 0, 0), ( 0,  0, -1), (0, -1,  0))
	]

	# capture environment map to cubemap
	# create rbo
	capture_rbo = glGenRenderbuffers(1)
	glBindRenderbuffer(GL_RENDERBUFFER, capture_rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, 512, 512)
	glBindRenderbuffer(GL_RENDERBUFFER, 0)

	# setup fbo
	capture_fbo = glGenFramebuffers(1)
	with fbo.bind(capture_fbo):
		# attach depth buffer
		glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, capture_rbo)
		
	# draw environment map to skybox
	glViewport(0,0,512,512)
	glActiveTexture(GL_TEXTURE0)
	glBindTexture(GL_TEXTURE_2D, environment_tex)
	with program.use(equirectangular_to_cubemap_program):
		program.set_uniform(equirectangular_to_cubemap_program, "equirectangularMap", 0)
		program.set_uniform(equirectangular_to_cubemap_program, "projectionMatrix", capture_projection)

		
		with fbo.bind(capture_fbo):
			for i in range(6):
				glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, env_cubemap, 0)	
				program.set_uniform(equirectangular_to_cubemap_program, "viewMatrix", capture_views[i])
				glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
				imdraw.cube(equirectangular_to_cubemap_program)


	# Image based lighting 
	# (create irradiance map for diffuse, and prefilter map for reflection ambient lighting)
	# ------------------------

	# create irradiance cubemap
	irradiance_map = glGenTextures(1)
	glBindTexture(GL_TEXTURE_CUBE_MAP, irradiance_map);
	for i in range(6):
		glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB16F, 32, 32, 0, GL_RGB, GL_FLOAT, None)

	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

	glBindRenderbuffer(GL_RENDERBUFFER, capture_rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, 32, 32)
	glBindRenderbuffer(GL_RENDERBUFFER, 0)

	# solve irradiance map
	with program.use(irradiance_program):
		program.set_uniform(irradiance_program, "environmentMap", 0)
		program.set_uniform(irradiance_program, "projectionMatrix", capture_projection)
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_CUBE_MAP, env_cubemap)

		glViewport(0, 0, 32, 32) # don't forget to configure the viewport to the capture dimensions.
		with fbo.bind(capture_fbo):
			for i in range(6):
				program.set_uniform(irradiance_program, "viewMatrix", capture_views[i]);
				glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, irradiance_map, 0)
				glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

				imdraw.cube(irradiance_program)

	# prefilter hdri map for specular IBL
	prefilterMap = glGenTextures(1)
	glBindTexture(GL_TEXTURE_CUBE_MAP, prefilterMap)
	for i in range(6):
		glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB16F, 128, 128, 0, GL_RGB, GL_FLOAT, None)

	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

	glGenerateMipmap(GL_TEXTURE_CUBE_MAP)

	""" COPY PASTE (+convert to python and my puregl) FROM> https://github.com/JoeyDeVries/LearnOpenGL/blob/master/src/6.pbr/2.2.1.ibl_specular/ibl_specular.cpp """
	
	# pbr: create a pre-filter cubemap, and re-scale capture FBO to pre-filter scale.
	prefilterMap = glGenTextures(1)
	glBindTexture(GL_TEXTURE_CUBE_MAP, prefilterMap)
	for i in range(6):
		glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB16F, 128, 128, 0, GL_RGB, GL_FLOAT, None)

	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR) # be sure to set minifcation filter to mip_linear 
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	# generate mipmaps for the cubemap so OpenGL automatically allocates the required memory.
	glGenerateMipmap(GL_TEXTURE_CUBE_MAP)

	# pbr: run a quasi monte-carlo simulation on the environment lighting to create a prefilter (cube)map.
	# ----------------------------------------------------------------------------------------------------
	
	with program.use(prefilterShader):
		program.set_uniform(prefilterShader, "environmentMap", 0)
		program.set_uniform(prefilterShader, "projectionMatrix", capture_projection)
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_CUBE_MAP, env_cubemap)

		with fbo.bind(capture_fbo):
			maxMipLevels = 5

			for mip in range(maxMipLevels):
				# resize framebuffer according to mip-level size.
				mipWidth  = int(128 * math.pow(0.5, mip))
				mipHeight = int(128 * math.pow(0.5, mip))
				glBindRenderbuffer(GL_RENDERBUFFER, capture_rbo);
				glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, mipWidth, mipHeight)
				glViewport(0, 0, mipWidth, mipHeight)

				roughness = mip / (maxMipLevels - 1)
				program.set_uniform(prefilterShader, "roughness", roughness)

				for i in range(6):
					program.set_uniform(prefilterShader, "viewMatrix", capture_views[i])
					glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, prefilterMap, mip)

					glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
					imdraw.cube(prefilterShader)

	# pbr: generate a 2D LUT from the BRDF equations used.
	# ----------------------------------------------------
	brdfLUTTexture = glGenTextures(1)

	# pre-allocate enough memory for the LUT texture.
	glBindTexture(GL_TEXTURE_2D, brdfLUTTexture)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RG16F, 512, 512, 0, GL_RG, GL_FLOAT, None);
	# be sure to set wrapping mode to GL_CLAMP_TO_EDGE
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

	# then re-configure capture framebuffer object and render screen-space quad with BRDF shader.
	with fbo.bind(capture_fbo):
		glBindRenderbuffer(GL_RENDERBUFFER, capture_rbo)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, 512, 512)
		glBindRenderbuffer(GL_RENDERBUFFER, 0)
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, brdfLUTTexture, 0)

	with program.use(brdfShader):
		with fbo.bind(capture_fbo):
			glViewport(0, 0, 512, 512)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			imdraw.quad(brdfShader)



""" END OF COPY PASTE"""

import time
def draw_scene(prog, projection_matrix, view_matrix):
	"""Draw scen with a shader program"""
	program.set_uniform(prog, 'projectionMatrix', projection_matrix)
	program.set_uniform(prog, 'viewMatrix', view_matrix)
	camera_pos = glm.inverse(view_matrix)[3].xyz
	program.set_uniform(prog, 'cameraPos', camera_pos)

	model_matrix = glm.translate(glm.mat4(1), (-1,0.5,0))
	normal_matrix = glm.mat3( glm.transpose(glm.inverse(model_matrix)) )
	program.set_uniform(prog, 'modelMatrix', model_matrix)
	program.set_uniform(prog, 'normalMatrix', normal_matrix)
	imdraw.cube(prog)

	model_matrix = glm.translate(glm.mat4(1), (1,0,0))
	normal_matrix = glm.mat3( glm.transpose(glm.inverse(model_matrix)) )
	program.set_uniform(prog, 'modelMatrix', model_matrix)
	program.set_uniform(prog, 'normalMatrix', normal_matrix)
	imdraw.sphere(prog)

	model_matrix = glm.mat4(1)
	normal_matrix = glm.mat3( glm.transpose(glm.inverse(model_matrix)) )
	program.set_uniform(prog, 'modelMatrix', model_matrix)
	program.set_uniform(prog, 'normalMatrix', normal_matrix)
	imdraw.plane(prog)


with window:
	while not window.should_close():
		# 1. render scene to depth map
		# ============================
		with fbo.bind(shadow_fbo):
			glViewport(0,0, shadow_fbo_width, shadow_fbo_height)
			glClear(GL_DEPTH_BUFFER_BIT)
			glCullFace(GL_FRONT)

			# configure shader
			light_projection = glm.ortho(-2,2,-2,2, 0.5,12)
			light_view = glm.lookAt((math.sin(time.time()*3)*5,5,2), (0,0,0), (0,1,0))

			with program.use(depth_program):
				draw_scene(depth_program, light_projection, light_view)

		# 2. Render the scene to HDR_FBO with shadow mapping
		# ==================================================
		with fbo.bind(hdr_fbo):
			glViewport(0, 0, hdr_fbo_width, hdr_fbo_height)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glCullFace(GL_BACK)

			# Render skybox
			# -------------
			glDepthFunc(GL_LEQUAL)
			glDepthMask(GL_FALSE)
			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_CUBE_MAP, env_cubemap)
			with program.use(skybox_program):
				program.set_uniform(skybox_program, 'projectionMatrix', window.projection_matrix)
				sky_view = glm.mat4(glm.mat3(window.view_matrix)); 
				program.set_uniform(skybox_program, 'viewMatrix', sky_view)
				camera_pos = glm.transpose(glm.transpose(glm.inverse(window.view_matrix)))[3].xyz
				program.set_uniform(skybox_program, 'cameraPos', camera_pos)
				program.set_uniform(skybox_program, 'skybox', 0)
				imdraw.cube(skybox_program)
			glDepthMask(GL_TRUE)
			glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

			# # Render scene with phong shading
			# # -------------------------------
			# with program.use(phong_program):
			# 	program.set_uniform(phong_program, 'projectionMatrix', window.projection_matrix)
			# 	program.set_uniform(phong_program, 'viewMatrix', window.view_matrix)
			# 	model_matrix = glm.identity(glm.mat4x4)
			# 	normal_matrix = glm.mat3( glm.transpose(glm.inverse(model_matrix)) )
			# 	program.set_uniform(phong_program, 'modelMatrix', model_matrix)
			# 	program.set_uniform(phong_program, 'normalMatrix', normal_matrix)

			# 	program.set_uniform(phong_program, 'material.diffuseMap', 0)
			# 	program.set_uniform(phong_program, 'material.specularMap', 1)
			# 	program.set_uniform(phong_program, 'material.shiness', 5.0)


			# 	light_dir = glm.normalize(glm.inverse(light_view)[2].xyz)
			# 	light_pos = glm.inverse(light_view)[3].xyz
			# 	program.set_uniform(phong_program, 'lightSpaceMatrix', light_projection * light_view)
			# 	program.set_uniform(phong_program, 'sun.direction', light_dir)
			# 	program.set_uniform(phong_program, 'sun.ambient', glm.vec3(0.3))
			# 	program.set_uniform(phong_program, 'sun.diffuse', glm.vec3(1))
			# 	program.set_uniform(phong_program, 'sun.specular', glm.vec3(1))
			# 	program.set_uniform(phong_program, 'sun.shadowMap', 2)

			# 	camera_pos = glm.inverse(window.view_matrix)[3].xyz
			# 	program.set_uniform(phong_program, 'cameraPos', camera_pos)
				
			# 	# draw geometry
			# 	glActiveTexture(GL_TEXTURE0+0)
			# 	glBindTexture(GL_TEXTURE_2D, diffuse_tex)
			# 	glActiveTexture(GL_TEXTURE0+1)
			# 	glBindTexture(GL_TEXTURE_2D, specular_tex)
			# 	glActiveTexture(GL_TEXTURE0+2)
			# 	glBindTexture(GL_TEXTURE_2D, shadow_tex)
			# 	glActiveTexture(GL_TEXTURE0+3)
			# 	glBindTexture(GL_TEXTURE_CUBE_MAP, skybox_tex)
			# 	draw_scene(phong_program, window.projection_matrix, window.view_matrix)

			# Render scene with PBR shading
			# -----------------------------
			with program.use(pbr_program):
				program.set_uniform(pbr_program, 'material.albedo', (0.5,0.0,0.0))
				program.set_uniform(pbr_program, 'material.roughness', 0.1)
				program.set_uniform(pbr_program, 'material.metallic', 0.0)
				program.set_uniform(pbr_program, 'material.ao', 1.0)

				light_dir = glm.normalize(glm.inverse(light_view)[2].xyz)
				light_pos = glm.inverse(light_view)[3].xyz
				program.set_uniform(pbr_program, 'lightSpaceMatrix', light_projection * light_view)
				program.set_uniform(pbr_program, 'light.direction', light_dir)
				program.set_uniform(pbr_program, 'light.position', light_pos)
				program.set_uniform(pbr_program, 'light.color', glm.vec3(10.0))

				program.set_uniform(pbr_program, 'irradianceMap', 3)
				program.set_uniform(pbr_program, 'prefilterMap', 4)
				program.set_uniform(pbr_program, 'brdfLUT', 5)
				program.set_uniform(pbr_program, 'shadowMap', 6)

				# draw geometry
				# material
				glActiveTexture(GL_TEXTURE0+0)
				glBindTexture(GL_TEXTURE_2D, diffuse_tex)
				glActiveTexture(GL_TEXTURE0+1)
				glBindTexture(GL_TEXTURE_2D, specular_tex)
				glActiveTexture(GL_TEXTURE0+2)
				glBindTexture(GL_TEXTURE_2D, shadow_tex)

				# IBL
				glActiveTexture(GL_TEXTURE0+3)
				glBindTexture(GL_TEXTURE_CUBE_MAP, irradiance_map)
				glActiveTexture(GL_TEXTURE0+4)
				glBindTexture(GL_TEXTURE_CUBE_MAP, prefilterMap)
				glActiveTexture(GL_TEXTURE0+5)
				glBindTexture(GL_TEXTURE_2D, brdfLUTTexture)
				glActiveTexture(GL_TEXTURE0+6)
				glBindTexture(GL_TEXTURE_2D, shadow_tex)

				draw_scene(pbr_program, window.projection_matrix, window.view_matrix)


		# 3. Render HDR color component on quad
		# ==================================
		# clear viweport
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		# tonemap HDR texture and blit to screen
		glViewport(0, 0, window.width, window.height)

		with program.use(tonamapping_program):
			program.set_uniform(tonamapping_program, 'projectionMatrix', np.eye(4))
			program.set_uniform(tonamapping_program, 'viewMatrix', np.eye(4))
			program.set_uniform(tonamapping_program, 'modelMatrix', np.eye(4))
			program.set_uniform(tonamapping_program, 'screenTexture', 0)
			program.set_uniform(tonamapping_program, 'exposure', -1.0)
			program.set_uniform(tonamapping_program, 'gamma', 2.2)
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_2D, hdr_tex)
			imdraw.quad(tonamapping_program)

		# Debug: Display light depth map
		# -----------------------------------------
		imdraw.texture(shadow_tex, (0,0,100,100), shuffle=(0,0,0,-1))
		imdraw.texture(hdr_tex, (0,100,100,100))

		# swap buffers
		window.swap_buffers()
		GLFWViewer.poll_events()

