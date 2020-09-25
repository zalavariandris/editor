from editor.render.graphics.passes import RenderPass
from OpenGL.GL import *
from editor.render import puregl, glsl, imdraw


class GaussianblurPass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, False, GL_BACK)
        self.program = None
        self.texture = None
        self.fbo = None

    def setup(self):
        super().setup()
        self.program = puregl.program.create(*glsl.read('gaussian'))

        self.bloom_blur_fbos = glGenFramebuffers(2)
        self.bloom_blur_texs = glGenTextures(2)
        for i in range(2):
            glBindFramebuffer(GL_FRAMEBUFFER, self.bloom_blur_fbos[i])
            glBindTexture(GL_TEXTURE_2D, self.bloom_blur_texs[i])
            glTexImage2D(
                GL_TEXTURE_2D, 0, GL_RGBA32F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None
            )
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.bloom_blur_texs[i], 0
            )

            assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def render(self, input_texture, iterations=2):
        super().render()

        horizontal = True
        first_iteration = True
        with puregl.program.use(self.program):
            for i in range(iterations*2):
                horizontal = i % 2
                glBindFramebuffer(GL_FRAMEBUFFER, self.bloom_blur_fbos[horizontal])
                glClearColor(0.0, 0.0, 0.0, 1.0)
                puregl.program.set_uniform(self.program, 'horizontal', horizontal)
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(
                    GL_TEXTURE_2D, input_texture if first_iteration else self.bloom_blur_texs[1 - horizontal]
                )
                imdraw.quad(self.program)
                if first_iteration:
                    first_iteration = False

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        return self.bloom_blur_texs[1]

if __name__ == "__main__":
    from editor.render.imdraw.examples.viewer import Viewer
    from editor.render import assets
    import glm
    import numpy as np
    # load assets
    img = (assets.imread("container2.png")[...,:3]/255).astype(np.float32)
    h, w, c = img.shape
    # create viewer
    viewer = Viewer(1024,512, "GaussianBlur example")
    blurpass = GaussianblurPass(viewer.width, viewer.height)

    @viewer.event
    def on_setup():
        global tex
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, w, h, 0, GL_RGB, GL_FLOAT, img)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glGenerateMipmap(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, 0)

    @viewer.event
    def on_draw():
        glDisable(GL_DEPTH_TEST)
        imdraw.texture(tex, (0,0,viewer.width//2,viewer.height))
        blurred = blurpass.render(tex, iterations=16)
        imdraw.texture(blurred, (viewer.width//2,0,viewer.width//2,viewer.height))

        
    viewer.start()

