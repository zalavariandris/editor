from OpenGL.GL import *
import numpy as np
import logging


class RenderPass:
    """
    Renderpass
    width, height
    depth_test
    cull_face
    blending
    """
    def __init__(self, width, height, depth_test=False, cull_face=False, blending=False, seamless_cubemap=False):
        # properties
        self.width = width
        self.height = height
        self.depth_test = depth_test
        self.cull_face = cull_face
        self.blending = blending
        self.seamless_cubemap = seamless_cubemap

        self._needs_setup = True

    @staticmethod
    def create_texture_from_data(data: np.ndarray, level=0, internal_format=None, format=None, type=None, min_filter=GL_LINEAR, mag_filter=GL_LINEAR, wrap_s=None, wrap_t=None, border_color=None):
        # validate data
        assert len(data.shape) == 3, "got: {}".format(data.shape)
        assert data.shape[2] in (1,2,3,4)

        # defaults
        height, width, channels = data.shape
        level = 0

        # TODO: handle more formats
        def format_from_data(data):
            if data.dtype == np.float32 and data.shape[2] == 3:
                return (GL_RGB32F, GL_RGB, GL_FLOAT)
            else: 
                raise NotImplementedError("{},{}".format(data.dtype, channels))

        glinternalformat, glformat, gltype = format_from_data(data)

        # create texture
        tex = glGenTextures(1)

        # upload data
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, level, glinternalformat, width, height, 0, glformat, gltype, data)

        # configure
        if min_filter:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, min_filter)
        if mag_filter:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, mag_filter)
        if wrap_s:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap_s)
        if wrap_t:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap_t)
        if border_color:
            glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array(border_color))

        glBindTexture(GL_TEXTURE_2D, 0)

        return tex

    def setup(self):
        logging.debug("setup {}".format(self.__class__.__name__))
        self._needs_setup = False

    def render(self, *args):
        if self._needs_setup:
            self.setup()
        if self.cull_face:
            glEnable(GL_CULL_FACE)
            glCullFace(self.cull_face)
        else:
            glDisable(GL_CULL_FACE)

        if self.depth_test:
            glEnable(GL_DEPTH_TEST)
        else:
            glDisable(GL_DEPTH_TEST)

        if self.blending:
            glEnable(GL_BLEND)
            glBlendFunc(*self.blending)
        else:
            glDisable(GL_BLEND)

        if self.seamless_cubemap:
            glEnable(GL_TEXTURE_CUBE_MAP_SEAMLESS)
        else:
            glDisable(GL_TEXTURE_CUBE_MAP_SEAMLESS)

        glViewport(0,0,self.width, self.height)

    def copy_buffer_from(self, source, buffers):
        if self._needs_setup:
            self.setup()
        glBindFramebuffer(GL_READ_FRAMEBUFFER, source.fbo)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.fbo)  # write to default framebuffer
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, buffers, GL_NEAREST)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
