from editor.render.graphics.passes.renderpass import RenderPass
from OpenGL.GL import *
from editor.render import puregl, glsl, assets
from editor.render.graphics import Scene
from editor.render.graphics.cameras import Camera360
import numpy as np


class EnvironmentPass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, True, GL_BACK, None)
        self.texture = None
        self.fbo = None
        self.program = None

    def setup(self):
        super().setup()
        # Create textures
        # ---------------
        self.texture = glGenTextures(1)

        # define textures
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.texture)
        for i in range(6):
                glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, 0, GL_RGB32F, 
                    self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

        # configure textures
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

        # create rbo
        rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        # Create fbo
        # ----------
        self.fbo = glGenFramebuffers(1)

        # configure fbo
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        # attach color textures
        # TODO: use geometry shader to render all sides in one pass 
        # see: https://learnopengl.com/Advanced-Lighting/Shadows/Point-Shadows

        # attach rbo
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rbo)

        # cleanup
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # Create program
        # --------------
        self.program = puregl.program.create(*glsl.read("graphics/environment"))

    def render(self, environment, camera: Camera360):
        super().render()
        with puregl.fbo.bind(self.fbo), puregl.program.use(self.program):
            #set viewport
            glViewport(0,0,self.width, self.height)
            glClearColor(0,0,0,1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # bind environment map to texture unit
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, environment)
            puregl.program.set_uniform(self.program, 'equirectangularMap', 0)

            # set camer aprojection
            puregl.program.set_uniform(self.program, "projectionMatrix", camera.projection)

            for i in range(6):
                # set camera view
                puregl.program.set_uniform(self.program, "viewMatrix", camera.views[i])

                # attach cubemap side to fbo color attachemnt
                glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, self.texture, 0) 
                
                # draw
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                puregl.imdraw.cube(self.program, flip=True)
            glBindTexture(GL_TEXTURE_2D, 0)

        return self.texture


if __name__ == "__main__":
    import glm
    from editor.render.graphics.viewer import Viewer
    from editor.render.graphics import Scene, Mesh, Geometry, Material
    import time, math

    viewer = Viewer(floating=True)
    environment_pass = EnvironmentPass(1024,1024)
    environment_image = assets.imread('hdri/Tropical_Beach_3k.hdr').astype(np.float32)

    environment_texture = None

    @viewer.on_setup
    def setup():
        global environment_texture
        environment_texture = RenderPass.create_texture_from_data(environment_image)
        environment_pass.setup()

    @viewer.on_draw
    def draw():
        global environment_texture
        # render passes
        camera360 = Camera360(transform=glm.mat4(1),
                              near=0.1, 
                              far=10)

        environment_cubemap = environment_pass.render(environment_texture, camera360)

        # render passes to screen
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        puregl.imdraw.texture(environment_texture, (0, 0, 190,190))
        puregl.imdraw.cubemap(environment_cubemap, (0,0,viewer.width, viewer.height), viewer.camera.projection, viewer.camera.view)
    
    viewer.start(worker=False)
    print("- end of program -")