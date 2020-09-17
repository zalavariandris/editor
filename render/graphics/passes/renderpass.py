from OpenGL.GL import *


class RenderPass:
    def __init__(self, width, height, depth_test, cull_face, blending):
        # properties
        self.width = width
        self.height = height
        self.depth_test = depth_test
        self.cull_face = cull_face
        self.blending = blending

    @staticmethod
    def create_texture(level, internalformat, width, height, format, type, data,
                       min_filter=None, mag_filter=None,
                       wrap_s=None, wrap_t=None):
        # generate texture
        # ----------------
        tex = glGenTextures(1)

        # define texture
        # --------------
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, level, internalformat, width, height, format, type, data)

        # configure texture
        # -----------------
        if min_filter:
            glTexParameteri(tex, GL_TEXTURE_MIN_FILTER, min_filter)
        if mag_filter:
            glTexParameteri(tex, GL_TEXTURE_MAG_FILTER, min_filter)
        if wrap_s:
            glTexParameteri(tex, GL_TEXTURE_MIN_FILTER, wrap_s)
        if wrap_t:
            glTexParameteri(tex, GL_TEXTURE_MIN_FILTER, wrap_t)
        glBindTexture(GL_TEXTURE_2D, 0)
        return tex

    @staticmethod
    def create_fbo(colors, depth=None, stencil=None):
        fbo = glGenFramebuffers(1)
        return fbo

    def setup(self):
        pass

    def render(self, *args):
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
