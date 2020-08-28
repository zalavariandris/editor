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

# load shader files
render_folder = "../"
surface_vs = Path(render_folder, 'glsl/surface.vs').read_text()
surface_fs = Path(render_folder, 'glsl/surface.fs').read_text()
lambert_vs = Path(render_folder, 'glsl/lambert.vs').read_text()
lambert_fs = Path(render_folder, 'glsl/lambert.fs').read_text()
phong_vs = Path(render_folder, 'glsl/phong.vs').read_text()
phong_fs = Path(render_folder, 'glsl/phong.fs').read_text()
pbr_vs = Path(render_folder, 'glsl/pbr.vs').read_text()
pbr_fs = Path(render_folder, 'glsl/pbr.fs').read_text()
simple_depth_vs = Path(render_folder, 'glsl/simple_depth_shader.vs').read_text()
simple_depth_fs = Path(render_folder, 'glsl/simple_depth_shader.fs').read_text()
debug_quad_vs = Path(render_folder, 'glsl/debug_quad.vs').read_text()
debug_quad_depth_fs = Path(render_folder, 'glsl/debug_quad_depth.fs').read_text()

# Init
width, height = 1024, 768
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

#
# read textures
#
def to_srgb(img, gamma=2.2):
	return np.power(img, (1/gamma, 1/gamma, 1/gamma))

def to_linear(img, gamma=2.2):
	return np.power(img, (gamma, gamma, gamma))

diffuse_data = np.array(Image.open(Path(render_folder, 'assets/container2_axis.png')))[...,[2,1,0]]/255
specular_data = np.array(Image.open(Path(render_folder, 'assets/container2_specular.png')))[...,[2,1,0]]/255
diffuse_data=to_linear(diffuse_data)
specular_data=to_linear(specular_data)

with window:
	glEnable(GL_PROGRAM_POINT_SIZE)
	glEnable(GL_DEPTH_TEST)
	
	# create material textures
	diffuse_tex = texture.create(diffuse_data, slot=0, format=GL_BGR)
	specular_tex = texture.create(specular_data, slot=1, format=GL_BGR)

	# create programs
	lambert_program = program.create(lambert_vs, lambert_fs)
	phong_program = program.create(phong_vs, phong_fs)
	pbr_program = program.create(pbr_vs, pbr_fs)

	# shadow mapping
	shadow_fbo = glGenFramebuffers(1)
	shadow_fbo_width, shadow_fbo_height = 1024, 1024
	glBindFramebuffer(GL_FRAMEBUFFER, shadow_fbo)
	shadow_tex = texture.create((shadow_fbo_width, shadow_fbo_height), 
					slot=2, 
					format=GL_DEPTH_COMPONENT,
					wrap_s=GL_CLAMP_TO_BORDER,
					wrap_t=GL_CLAMP_TO_BORDER, 
					border_color=(1.0, 1.0, 1.0, 1.0))
	glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, shadow_tex, 0)
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
	glDrawBuffer(GL_NONE) # dont render color data
	glReadBuffer(GL_NONE)
	glBindFramebuffer(GL_FRAMEBUFFER, 0)
	depth_program = program.create(simple_depth_vs, simple_depth_fs)
	debug_depth_program = program.create(debug_quad_vs, debug_quad_depth_fs)

	# high dynamic range fbo
	# ----------------------
	hdr_fbo = glGenFramebuffers(1)
	hdr_fbo_width, hdr_fbo_height = width, height # initalize FBO with window size
	glBindFramebuffer(GL_FRAMEBUFFER, hdr_fbo)

	# attach color attachment
	hdr_tex = glGenTextures(1)
	glActiveTexture(GL_TEXTURE0)
	glBindTexture(GL_TEXTURE_2D, hdr_tex)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, hdr_fbo_width, hdr_fbo_height, 0, GL_RGB, GL_FLOAT, None)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, hdr_tex, 0)

	# attach depth and stencil renderbuffers
	rbo = glGenRenderbuffers(1)
	glBindRenderbuffer(GL_RENDERBUFFER, rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, hdr_fbo_width, hdr_fbo_height)
	glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
	
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
	glBindTexture(GL_TEXTURE_2D, 0)
	glBindRenderbuffer(GL_RENDERBUFFER, 0)

	tonamapping_program = program.create(Path(render_folder, "glsl/tonemapping.vs").read_text(), Path(render_folder, "glsl/tonemapping.fs").read_text())

	# environment map
	# ---------------
	faces = [
		Path(render_folder, "assets/Storforsen3/posx.jpg"),
		Path(render_folder, "assets/Storforsen3/negx.jpg"),
		Path(render_folder, "assets/Storforsen3/posy.jpg"),
		Path(render_folder, "assets/Storforsen3/negy.jpg"),
		Path(render_folder, "assets/Storforsen3/posz.jpg"),
		Path(render_folder, "assets/Storforsen3/negz.jpg"),
	]

	skybox_data = [to_linear(np.array(Image.open(file))/255) for i, file in enumerate(faces)]
	def load_cubemap(faces):
		cubemap = glGenTextures(1)
		glBindTexture(GL_TEXTURE_CUBE_MAP, cubemap)

		for i, data in enumerate(skybox_data):
			height, width, channels = data.shape
			glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i,
				0, GL_RGB, width, height, 0, GL_RGB, GL_FLOAT, data
			)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)  
		return cubemap

	skybox_positions = np.array([
		# positions          
		-1.0,  1.0, -1.0,
		-1.0, -1.0, -1.0,
		 1.0, -1.0, -1.0,
		 1.0, -1.0, -1.0,
		 1.0,  1.0, -1.0,
		-1.0,  1.0, -1.0,

		-1.0, -1.0,  1.0,
		-1.0, -1.0, -1.0,
		-1.0,  1.0, -1.0,
		-1.0,  1.0, -1.0,
		-1.0,  1.0,  1.0,
		-1.0, -1.0,  1.0,

		 1.0, -1.0, -1.0,
		 1.0, -1.0,  1.0,
		 1.0,  1.0,  1.0,
		 1.0,  1.0,  1.0,
		 1.0,  1.0, -1.0,
		 1.0, -1.0, -1.0,

		-1.0, -1.0,  1.0,
		-1.0,  1.0,  1.0,
		 1.0,  1.0,  1.0,
		 1.0,  1.0,  1.0,
		 1.0, -1.0,  1.0,
		-1.0, -1.0,  1.0,

		-1.0,  1.0, -1.0,
		 1.0,  1.0, -1.0,
		 1.0,  1.0,  1.0,
		 1.0,  1.0,  1.0,
		-1.0,  1.0,  1.0,
		-1.0,  1.0, -1.0,

		-1.0, -1.0, -1.0,
		-1.0, -1.0,  1.0,
		 1.0, -1.0, -1.0,
		 1.0, -1.0, -1.0,
		-1.0, -1.0,  1.0,
		 1.0, -1.0,  1.0
	], dtype=np.float32).reshape(-1,3)
	skybox_tex = load_cubemap(faces)
	skybox_program = program.create(Path(render_folder,'glsl/skybox.vs').read_text(), Path(render_folder, 'glsl/skybox.fs').read_text())
	skyboxVAO, skyboxVBO = glGenVertexArrays(1), glGenBuffers(1)
	glBindVertexArray(skyboxVAO)
	glBindBuffer(GL_ARRAY_BUFFER, skyboxVBO)
	glBufferData(GL_ARRAY_BUFFER, skybox_positions.nbytes, skybox_positions, GL_STATIC_DRAW)
	glEnableVertexAttribArray(0)
	location = glGetAttribLocation(skybox_program, 'position')
	glVertexAttribPointer(location,3, GL_FLOAT, False, 0, None)

	# Prepare Environment map
	# ----------------------
	# setup fbo
	capture_fbo =glGenFramebuffers(1)
	capture_rbo = glGenRenderbuffers(1)
	glBindFramebuffer(GL_FRAMEBUFFER, capture_fbo) #FIXME: are we actually need depth buffer rbo 
													#to capture an environment map to cubemap?
	glBindRenderbuffer(GL_RENDERBUFFER, capture_rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24,512,512)
	glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, capture_rbo)

	# read image
	environment_data = imageio.imread(Path(render_folder, 'assets/hdri/Tropical_Beach_3k.hdr'), format="HDR-FI")
	env_height, env_width, env_channels = environment_data.shape

	# create env texture
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

	# convert equirectangular environment to cubemap
	equirectangular_to_cubemap_program = program.create(Path(render_folder,'glsl/cubemap.vs').read_text(), Path(render_folder, 'glsl/equirectangular_to_cubemap.fs').read_text())

	glUseProgram(equirectangular_to_cubemap_program)
	program.set_uniform(equirectangular_to_cubemap_program, "equirectangularMap", 0)
	program.set_uniform(equirectangular_to_cubemap_program, "projectionMatrix", capture_projection)
	glActiveTexture(GL_TEXTURE0)
	glBindTexture(GL_TEXTURE_2D, environment_tex)

	glViewport(0,0,512,512)
	glBindFramebuffer(GL_FRAMEBUFFER, capture_fbo)
	for i in range(6):
		program.set_uniform(equirectangular_to_cubemap_program, "viewMatrix", capture_views[i])
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, env_cubemap, 0)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		imdraw.cube(capture_fbo)
	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	# crate irradiance cubemap
	irradiance_map = glGenTextures(1)
	glBindTexture(GL_TEXTURE_CUBE_MAP, irradiance_map);
	for i in range(6):
		glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB16F, 32, 32, 0, GL_RGB, GL_FLOAT, None)

	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

	glBindFramebuffer(GL_FRAMEBUFFER, capture_fbo)
	glBindRenderbuffer(GL_RENDERBUFFER, capture_rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, 32, 32)

	# solve irradiance map
	irradiance_program = program.create(Path(render_folder,'glsl/cubemap.vs').read_text(), Path(render_folder, 'glsl/irradiance_convolution.fs').read_text())
	glUseProgram(irradiance_program)
	program.set_uniform(irradiance_program, "environmentMap", 0)
	program.set_uniform(irradiance_program, "projectionMatrix", capture_projection)
	glActiveTexture(GL_TEXTURE0)
	glBindTexture(GL_TEXTURE_CUBE_MAP, env_cubemap)

	glViewport(0, 0, 32, 32) # don't forget to configure the viewport to the capture dimensions.
	glBindFramebuffer(GL_FRAMEBUFFER, capture_fbo)
	for i in range(6):
		program.set_uniform(irradiance_program, "viewMatrix", capture_views[i]);
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, irradiance_map, 0)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		imdraw.cube(irradiance_program)

	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	# prefilet hdri map for specular IBL
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
	# --------------------------------------------------------------------------------
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
	prefilterShader = program.create(Path(render_folder,'glsl/cubemap.vs').read_text(), Path(render_folder, 'glsl/prefilter.fs').read_text())
	glUseProgram(prefilterShader)
	program.set_uniform(prefilterShader, "environmentMap", 0)
	program.set_uniform(prefilterShader, "projectionMatrix", capture_projection)
	glActiveTexture(GL_TEXTURE0)
	glBindTexture(GL_TEXTURE_CUBE_MAP, env_cubemap)

	glBindFramebuffer(GL_FRAMEBUFFER, capture_fbo)
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

	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	# pbr: generate a 2D LUT from the BRDF equations used.
	# ----------------------------------------------------
	brdfShader = program.create(Path(render_folder,"glsl/brdf.vs").read_text(), Path(render_folder,"glsl/brdf.fs").read_text())
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
	glBindFramebuffer(GL_FRAMEBUFFER, capture_fbo)
	glBindRenderbuffer(GL_RENDERBUFFER, capture_rbo)
	glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, 512, 512)
	glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, brdfLUTTexture, 0)

	glViewport(0, 0, 512, 512)
	glUseProgram(brdfShader)
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	imdraw.quad(brdfShader)

	glBindFramebuffer(GL_FRAMEBUFFER, 0)

""" END OF COPY PASTE"""

import time
# Draw
def draw_scene(prog, projection_matrix, view_matrix):
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
		glBindFramebuffer(GL_FRAMEBUFFER, shadow_fbo)
		
		glViewport(0,0, shadow_fbo_width, shadow_fbo_height)
		glClear(GL_DEPTH_BUFFER_BIT)
		glCullFace(GL_FRONT)

		# configure shader
		light_projection = glm.ortho(-2,2,-2,2, 0.5,12)
		light_view = glm.lookAt((math.sin(time.time()*3)*5,5,2), (0,0,0), (0,1,0))

		glUseProgram(depth_program)

		
		draw_scene(depth_program, light_projection, light_view)
		
		glBindFramebuffer(GL_FRAMEBUFFER, 0)

		# 2. Render the scene to HDR_FBO with shadow mapping
		# ==================================================
		glBindFramebuffer(GL_FRAMEBUFFER, hdr_fbo)
		glViewport(0, 0, hdr_fbo_width, hdr_fbo_height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glCullFace(GL_BACK)

		# Render skybox
		glDepthFunc(GL_LEQUAL)
		glDepthMask(GL_FALSE)
		glUseProgram(skybox_program)
		program.set_uniform(skybox_program, 'projectionMatrix', window.projection_matrix)
		sky_view = glm.mat4(glm.mat3(window.view_matrix)); 
		program.set_uniform(skybox_program, 'viewMatrix', sky_view)
		camera_pos = glm.transpose(glm.transpose(glm.inverse(window.view_matrix)))[3].xyz
		program.set_uniform(skybox_program, 'cameraPos', camera_pos)
		glBindVertexArray(skyboxVAO)
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_CUBE_MAP, env_cubemap)
		glDrawArrays(GL_TRIANGLES, 0, 36)
		glDepthMask(GL_TRUE)

		# # Render scene with phong shading
		# # -------------------------------
		# glUseProgram(phong_program)
		# program.set_uniform(phong_program, 'projectionMatrix', window.projection_matrix)
		# program.set_uniform(phong_program, 'viewMatrix', window.view_matrix)
		# model_matrix = glm.identity(glm.mat4x4)
		# normal_matrix = glm.mat3( glm.transpose(glm.inverse(model_matrix)) )
		# program.set_uniform(phong_program, 'modelMatrix', model_matrix)
		# program.set_uniform(phong_program, 'normalMatrix', normal_matrix)

		# program.set_uniform(phong_program, 'material.diffuseMap', 0)
		# program.set_uniform(phong_program, 'material.specularMap', 1)
		# program.set_uniform(phong_program, 'material.shiness', 5.0)


		# light_dir = glm.normalize(glm.inverse(light_view)[2].xyz)
		# light_pos = glm.inverse(light_view)[3].xyz
		# program.set_uniform(phong_program, 'lightSpaceMatrix', light_projection * light_view)
		# program.set_uniform(phong_program, 'sun.direction', light_dir)
		# program.set_uniform(phong_program, 'sun.ambient', glm.vec3(0.3))
		# program.set_uniform(phong_program, 'sun.diffuse', glm.vec3(1))
		# program.set_uniform(phong_program, 'sun.specular', glm.vec3(1))
		# program.set_uniform(phong_program, 'sun.shadowMap', 2)

		# camera_pos = glm.inverse(window.view_matrix)[3].xyz
		# program.set_uniform(phong_program, 'cameraPos', camera_pos)
		
		# # draw geometry
		# glActiveTexture(GL_TEXTURE0+0)
		# glBindTexture(GL_TEXTURE_2D, diffuse_tex)
		# glActiveTexture(GL_TEXTURE0+1)
		# glBindTexture(GL_TEXTURE_2D, specular_tex)
		# glActiveTexture(GL_TEXTURE0+2)
		# glBindTexture(GL_TEXTURE_2D, shadow_tex)
		# glActiveTexture(GL_TEXTURE0+3)
		# glBindTexture(GL_TEXTURE_CUBE_MAP, skybox_tex)
		# draw_scene(phong_program, window.projection_matrix, window.view_matrix)
		# glBindFramebuffer(GL_FRAMEBUFFER, 0)

		# Render scene with PBR shading
		# -----------------------------
		glUseProgram(pbr_program)

		program.set_uniform(pbr_program, 'material.albedo', glm.vec3(0.3))
		program.set_uniform(pbr_program, 'material.roughness', 0.2)
		program.set_uniform(pbr_program, 'material.metallic', 0.0)
		program.set_uniform(pbr_program, 'material.ao', 1.0)

		light_dir = glm.normalize(glm.inverse(light_view)[2].xyz)
		light_pos = glm.inverse(light_view)[3].xyz
		program.set_uniform(pbr_program, 'lightSpaceMatrix', light_projection * light_view)
		program.set_uniform(pbr_program, 'light.direction', light_dir)
		program.set_uniform(pbr_program, 'light.position', light_pos)
		program.set_uniform(pbr_program, 'light.color', glm.vec3(1.0))

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

		glBindFramebuffer(GL_FRAMEBUFFER, 0)

		# Debug: Render fbo depth component on quad
		# -----------------------------------------
		# glViewport(0, 0, window.width, window.height)
		# glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		# glUseProgram(debug_depth_program)

		# program.set_uniform(debug_depth_program, 'projectionMatrix', np.eye(4))
		# program.set_uniform(debug_depth_program, 'viewMatrix', np.eye(4))
		# program.set_uniform(debug_depth_program, 'modelMatrix', np.eye(4))
		# program.set_uniform(debug_depth_program, 'depthMap', 2)
		# glActiveTexture(GL_TEXTURE0+2)
		# glBindTexture(GL_TEXTURE_2D, shadow_tex)
		# imdraw.quad(debug_depth_program)

		# 3. Render HDR color component on quad
		# ==================================
		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glUseProgram(tonamapping_program)

		program.set_uniform(tonamapping_program, 'projectionMatrix', np.eye(4))
		program.set_uniform(tonamapping_program, 'viewMatrix', np.eye(4))
		program.set_uniform(tonamapping_program, 'modelMatrix', np.eye(4))
		program.set_uniform(tonamapping_program, 'screenTexture', 0)
		program.set_uniform(tonamapping_program, 'exposure', 0.0)
		program.set_uniform(tonamapping_program, 'gamma', 2.2)
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_2D, hdr_tex)
		imdraw.quad(tonamapping_program)

		# swap buffers
		window.swap_buffers()
		GLFWViewer.poll_events()

