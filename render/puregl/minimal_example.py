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
phong_vs = Path('../glsl/phong.vs').read_text()
phong_fs = Path('../glsl/phong.fs').read_text()
simple_depth_vs = Path('../glsl/simple_depth_shader.vs').read_text()
simple_depth_fs = Path('../glsl/simple_depth_shader.fs').read_text()
debug_quad_vs = Path('../glsl/debug_quad.vs').read_text()
debug_quad_depth_fs = Path('../glsl/debug_quad_depth.fs').read_text()

# Init
width, height = 640, 480
model_matrix = np.identity(4)
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

# create geometry
diffuse_data = np.array(Image.open('../assets/container2.png'))[...,[2,1,0]]/255
specular_data = np.array(Image.open('../assets/container2_specular.png'))[...,[2,1,0]]/255

with window:
	glEnable(GL_PROGRAM_POINT_SIZE)
	glEnable(GL_DEPTH_TEST)

	print('type:', type(GL_RGB))
	texture.bind(diffuse_data, slot=0, format=GL_BGR)
	texture.bind(specular_data, slot=1, format=GL_BGR)
	depth_tex = texture.bind((1024, 1024), 
		                     slot=2, 
		                     format=GL_DEPTH_COMPONENT,
		                     wrap_s=GL_CLAMP_TO_BORDER,
		                     wrap_t=GL_CLAMP_TO_BORDER, 
		                     border_color=(1.0, 1.0, 1.0, 1.0))
	
	# create program
	phong_program = program.create(phong_vs, phong_fs)

	# create lights
	depthfbo = glGenFramebuffers(1)
	
	# attach depthmap to framebuffer
	glBindFramebuffer(GL_FRAMEBUFFER, depthfbo)
	glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, depth_tex, 0)
	assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
	glDrawBuffer(GL_NONE) # dont render color data
	glReadBuffer(GL_NONE)
	glBindFramebuffer(GL_FRAMEBUFFER, 0)

	# create depth program
	depth_program = program.create(simple_depth_vs, simple_depth_fs)

	# create display depth component program
	debug_depth_program = program.create(debug_quad_vs, debug_quad_depth_fs)


import time
# Draw
with window:
	while not window.should_close():
		# 1. render scene to depth map
		glBindFramebuffer(GL_FRAMEBUFFER, depthfbo)
		
		glViewport(0,0, 1024, 1024)
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

		# 2. render the scene as normal with shdow mapping
		# clear window
		glViewport(0, 0, window.width, window.height)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glCullFace(GL_BACK)
		
		# configure shader
		glUseProgram(phong_program)
		program.set_uniform(phong_program, 'projectionMatrix', window.projection_matrix)
		program.set_uniform(phong_program, 'viewMatrix', np.array(window.view_matrix))
		program.set_uniform(phong_program, 'modelMatrix', np.eye(4))
		program.set_uniform(phong_program, 'lightSpaceMatrix', light_projection * light_view)
		program.set_uniform(phong_program, 'diffuseMap', 0)
		program.set_uniform(phong_program, 'shadowMap', 2)
		light_pos = glm.normalize(glm.inverse(light_view)[2]).xyz
		program.set_uniform(phong_program, 'lightDir', light_pos)
		
		# draw geometry
		draw.cube(phong_program)
		draw.plane(phong_program)

		# # render fbo depth component on quad
		# glDisable(GL_CULL_FACE);
		# glUseProgram(debug_depth_program)
		# debug_depth_program = program.use(phong_vs, debug_quad_depth_fs)

		# program.set_uniform(debug_depth_program, 'projectionMatrix', np.eye(4))
		# program.set_uniform(debug_depth_program, 'viewMatrix', np.eye(4))
		# program.set_uniform(debug_depth_program, 'modelMatrix', np.eye(4))
		# program.set_uniform(debug_depth_program, 'depthMap', 2)
		# draw.quad(debug_depth_program)

		# swap buffers
		window.swap_buffers()
		GLFWViewer.poll_events()