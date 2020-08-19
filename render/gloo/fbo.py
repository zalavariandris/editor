from OpenGL.GL import *
from .texture import Texture

class FBO:
    def __init__(self, width, height, slot):
        self.texture_unit = slot
        self._handle = glGenFramebuffers(1)

        glBindFramebuffer(GL_FRAMEBUFFER, self._handle);
        
        # color buffer
        self.texture = Texture.from_size((width, height), slot)

        # depth buffer
        depthrenderbuffer = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, depthrenderbuffer)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, width, height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depthrenderbuffer)

        # Set "renderedTexture" as our colour attachement #0
        glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.texture._handle, 0);

        # Set the list of draw buffers.
        glDrawBuffers(1, [GL_COLOR_ATTACHMENT0])

        # Always check that our framebuffer is ok
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise Exception("bad framebuffer")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def __enter__(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self._handle)

    def __exit__(self, type, value, traceback):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def __del__(self):
        pass
        # glDeleteFrameBuffers(1, [self._handle])

