from OpenGL.GL import *
import numpy as np
from functools import singledispatch

@singledispatch
def create(*args, **kwargs):
	raise NotImplementedError

@create.register
def create_with_data(data: np.ndarray, slot, format, wrap_s=None, wrap_t=None, border_color=None):
	tex = glGenTextures(1)
	glActiveTexture(GL_TEXTURE0+slot)
	glBindTexture(GL_TEXTURE_2D, tex)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	if wrap_s:
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap_s)
	if wrap_t:
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap_t)
	if border_color:
		glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array(border_color))
	
	internalformat = {
		GL_RGB: GL_RGB,
		GL_BGR: GL_RGB,
		GL_DEPTH_COMPONENT: GL_DEPTH_COMPONENT
	}[format]
	#FIXME: read internal and formats https://www.khronos.org/registry/OpenGL-Refpages/gl4/html/glTexImage2D.xhtml
	glTexImage2D(GL_TEXTURE_2D, 0, internalformat, data.shape[1], data.shape[0], 0, format, GL_FLOAT, data)
	glBindTexture(GL_TEXTURE_2D, 0)

	return tex

import typing

@create.register
def create_with_size(size: tuple, slot, format, wrap_s=None, wrap_t=None, border_color=None):
	tex = glGenTextures(1)
	glActiveTexture(GL_TEXTURE0+slot)
	glBindTexture(GL_TEXTURE_2D, tex)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	if wrap_s:
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap_s)
	if wrap_t:
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap_t)
	if border_color:
		glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array(border_color))
	
	internalformat = {
		GL_RGB: GL_RGB,
		GL_BGR: GL_RGB,
		GL_DEPTH_COMPONENT: GL_DEPTH_COMPONENT
	}[format]
	glTexImage2D(GL_TEXTURE_2D, 0, internalformat, size[0], size[1], 0, format, GL_FLOAT, None)
	glBindTexture(GL_TEXTURE_2D, 0)
	return tex