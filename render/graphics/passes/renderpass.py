from OpenGL.GL import *


class RenderPass:
    def __init__(self, width, height, depth_test, cull_face, blending):
        # properties
        self.width = width
        self.height = height
        self.depth_test = depth_test
        self.cull_face = cull_face
        self.blending = blending

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
            glBlendFunc(*blending)
        else:
            glDisable(GL_BLEND)
