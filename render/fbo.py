from OpenGL.GL import *

class FBO:
    def __init__(self, width, height):
        self._handle = glGenFramebuffers(1)

        glBindFramebuffer(GL_FRAMEBUFFER, self._handle);
        # color buffer
        rendered_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, rendered_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        # depth buffer
        depthrenderbuffer = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, depthrenderbuffer)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, width, height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depthrenderbuffer)

        # Set "renderedTexture" as our colour attachement #0
        glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, rendered_texture, 0);

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

