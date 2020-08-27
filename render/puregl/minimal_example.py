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

# puregl
import program
import draw
import texture

# load shader files
render_folder = "../"
phong_vs = Path(render_folder, 'glsl/phong.vs').read_text()
phong_fs = Path(render_folder, 'glsl/phong.fs').read_text()
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
# gamma correct textures
def to_srgb(img, gamma=2.2):
	return np.power(img, (1/gamma, 1/gamma, 1/gamma))

def to_linear(img, gamma=2.2):
	return np.power(img, (gamma, gamma, gamma))

diffuse_data = np.array(Image.open(Path(render_folder, 'assets/container2.png')))[...,[2,1,0]]/255
specular_data = np.array(Image.open(Path(render_folder, 'assets/container2_specular.png')))[...,[2,1,0]]/255
diffuse_data=to_linear(diffuse_data)
specular_data=to_linear(specular_data)

with window:
	glEnable(GL_PROGRAM_POINT_SIZE)
	glEnable(GL_DEPTH_TEST)
	
	# phong shading
	diffuse_tex = texture.create(diffuse_data, slot=0, format=GL_BGR)
	specular_tex = texture.create(specular_data, slot=1, format=GL_BGR)
	phong_program = program.create(phong_vs, phong_fs)

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

	# 
	# high dynamic range fbo
	#
	hdr_fbo = glGenFramebuffers(1)
	hdr_fbo_width, hdr_fbo_height = width, height # initalize FBO with window size
	glBindFramebuffer(GL_FRAMEBUFFER, hdr_fbo)

	# attach color attachment
	hdr_tex = glGenTextures(1)
	glActiveTexture(GL_TEXTURE0)
	glBindTexture(GL_TEXTURE_2D, hdr_tex)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, hdr_fbo_width, hdr_fbo_height, 0, GL_RGB, GL_FLOAT, None)
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

	#
	# environment map
	#
	faces = [
		Path(render_folder, "assets/Yokohama3/posx.jpg"),
		Path(render_folder, "assets/Yokohama3/negx.jpg"),
		Path(render_folder, "assets/Yokohama3/posy.jpg"),
		Path(render_folder, "assets/Yokohama3/negy.jpg"),
		Path(render_folder, "assets/Yokohama3/posz.jpg"),
		Path(render_folder, "assets/Yokohama3/negz.jpg"),
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
    ], dtype=np.float32)
	skybox_tex = load_cubemap(faces)
	skybox_program = program.create(Path(render_folder,'glsl/skybox.vs').read_text(), Path(render_folder, 'glsl/skybox.fs').read_text())
	skyboxVAO, skyboxVBO = glGenVertexArrays(1), glGenBuffers(1)
	glBindVertexArray(skyboxVAO)
	glBindBuffer(GL_ARRAY_BUFFER, skyboxVBO)
	glBufferData(GL_ARRAY_BUFFER, skybox_positions.nbytes, skybox_positions, GL_STATIC_DRAW)
	glEnableVertexAttribArray(0)
	location = glGetAttribLocation(skybox_program, 'position')
	glVertexAttribPointer(location,3, GL_FLOAT, False, 0, None)


import time
# Draw
with window:
	while not window.should_close():
		# 1. render scene to depth map
		glBindFramebuffer(GL_FRAMEBUFFER, shadow_fbo)
		
		glViewport(0,0, shadow_fbo_width, shadow_fbo_height)
		glClear(GL_DEPTH_BUFFER_BIT)
		glCullFace(GL_FRONT)

		# configure shader
		light_projection = glm.ortho(-2,2,-2,2, 0.5,12)
		light_view = glm.lookAt((math.sin(time.time()*3)*5,5,-1), (0,0,0), (0,1,0))

		glUseProgram(depth_program)
		program.set_uniform(depth_program, 'projectionMatrix', light_projection)
		program.set_uniform(depth_program, 'viewMatrix', light_view)
		program.set_uniform(depth_program, 'modelMatrix', np.eye(4))
		
		# draw geometry
		draw.cube(phong_program)
		draw.plane(phong_program)
		
		glBindFramebuffer(GL_FRAMEBUFFER, 0)

		#
		# 2. render the scene to HDR_FBO with shadow mapping
		# 
		glBindFramebuffer(GL_FRAMEBUFFER, hdr_fbo)
		glViewport(0, 0, hdr_fbo_width, hdr_fbo_height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glCullFace(GL_BACK)

		# # Render skybox
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
		glBindTexture(GL_TEXTURE_CUBE_MAP, skybox_tex)
		glDrawArrays(GL_TRIANGLES, 0, 36)
		glDepthMask(GL_TRUE)

		# Render scene
		glUseProgram(phong_program)
		program.set_uniform(phong_program, 'projectionMatrix', window.projection_matrix)
		program.set_uniform(phong_program, 'viewMatrix', window.view_matrix)
		program.set_uniform(phong_program, 'modelMatrix', np.eye(4))
		program.set_uniform(phong_program, 'lightSpaceMatrix', light_projection * light_view)
		program.set_uniform(phong_program, 'material.diffuseMap', 0)
		program.set_uniform(phong_program, 'material.specularMap', 1)
		program.set_uniform(phong_program, 'material.environmentMap', 3)
		light_dir = glm.normalize(glm.inverse(light_view)[2]).xyz
		program.set_uniform(phong_program, 'sun.lightDir', light_dir)
		program.set_uniform(phong_program, 'sun.shadowMap', 2)
		camera_pos = glm.transpose(glm.transpose(glm.inverse(window.view_matrix)))[3].xyz
		program.set_uniform(phong_program, 'cameraPos', camera_pos)
		
		# draw geometry
		glActiveTexture(GL_TEXTURE0+0)
		glBindTexture(GL_TEXTURE_2D, diffuse_tex)
		glActiveTexture(GL_TEXTURE0+1)
		glBindTexture(GL_TEXTURE_2D, specular_tex)
		glActiveTexture(GL_TEXTURE0+2)
		glBindTexture(GL_TEXTURE_2D, shadow_tex)
		# glActiveTexture(GL_TEXTURE0+3)
		# glBindTexture(GL_TEXTURE_CUBE_MAP, skybox_tex)
		draw.cube(phong_program)
		draw.plane(phong_program)
		glBindFramebuffer(GL_FRAMEBUFFER, 0)

		# #
		# # render fbo depth component on quad
		# #
		# glViewport(0, 0, window.width, window.height)
		# glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		# glUseProgram(debug_depth_program)

		# program.set_uniform(debug_depth_program, 'projectionMatrix', np.eye(4))
		# program.set_uniform(debug_depth_program, 'viewMatrix', np.eye(4))
		# program.set_uniform(debug_depth_program, 'modelMatrix', np.eye(4))
		# program.set_uniform(debug_depth_program, 'depthMap', 2)
		# glActiveTexture(GL_TEXTURE0+2)
		# glBindTexture(GL_TEXTURE_2D, shadow_tex)
		# draw.quad(debug_depth_program)

		#
		# render HDR color component on quad
		#
		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glUseProgram(tonamapping_program)

		program.set_uniform(tonamapping_program, 'projectionMatrix', np.eye(4))
		program.set_uniform(tonamapping_program, 'viewMatrix', np.eye(4))
		program.set_uniform(tonamapping_program, 'modelMatrix', np.eye(4))
		program.set_uniform(tonamapping_program, 'screenTexture', 0)
		program.set_uniform(tonamapping_program, 'exposure', 2.0)
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_2D, hdr_tex)
		draw.quad(tonamapping_program)

		# swap buffers
		window.swap_buffers()
		GLFWViewer.poll_events()

