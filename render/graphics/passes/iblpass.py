from editor.render.graphics.passes.renderpass import RenderPass
from OpenGL.GL import *
from editor.render import puregl, glsl, assets
from editor.render.graphics import Scene
from editor.render.graphics.cameras import Camera360
import numpy as np
from environmentpass import EnvironmentPass

class IrradiancePass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, seamless_cubemap=True)

        # input
        self.environment = None
        self.irradiance = None

    def setup(self):
        # Create textures
        # ---------------
        self.irradiance = glGenTextures(1)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.irradiance)
        for i in range(6):
            glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

        # create rbo
        rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        # Create fbo
        # ----------
        self.fbo = glGenFramebuffers(1)
        with puregl.fbo.bind(self.fbo):
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rbo)
        

        # Create program
        # --------------
        self.program = puregl.program.create(*glsl.read('cubemap.vs', 'irradiance_convolution.fs'))


    def render(self, environment, camera: Camera360):
        super().render()
        # solve irradiance map
        with puregl.program.use(self.program):
            puregl.program.set_uniform(self.program, "environmentMap", 0)
            puregl.program.set_uniform(self.program, "projectionMatrix", camera.projection)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_CUBE_MAP, environment)

            glViewport(0, 0, self.width, self.width) # don't forget to configure the viewport to the capture dimensions.
            with puregl.fbo.bind(self.fbo):
                for i in range(6):
                    puregl.program.set_uniform(self.program, "viewMatrix", camera.views[i]);
                    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, self.irradiance, 0)
                    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                    puregl.imdraw.cube(self.program, flip=True)

        return self.irradiance


class PrefilterPass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, seamless_cubemap=True)

        # input
        self.environment = None
        self.prefilter = None
        self.program = None
        
    def setup(self):
        super().setup()
        # create shader
        self.program = puregl.program.create(*glsl.read('cubemap.vs', 'prefilter.fs'))

        # create texture
        self.prefilter = glGenTextures(1)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.prefilter)
        for i in range(6):
            glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB32F, 128, 128, 0, GL_RGB, GL_FLOAT, None)

        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glGenerateMipmap(GL_TEXTURE_CUBE_MAP)

        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

        # create rbo
        self.rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        # create fbo
        self.fbo = glGenFramebuffers(1)
        # attach depth buffer
        with puregl.fbo.bind(self.fbo):
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.rbo)
        
    def render(self, environment, camera: Camera360):
        super().render()
        # run a quasi monte-carlo simulation on the environment lighting to create a prefilter (cube)map.
        with puregl.program.use(self.program):
            puregl.program.set_uniform(self.program, "environmentMap", 0)
            puregl.program.set_uniform(self.program, "projectionMatrix", camera.projection)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_CUBE_MAP, environment)

            with puregl.fbo.bind(self.fbo):
                maxMipLevels = 5

                for mip in range(maxMipLevels):
                    # resize framebuffer according to mip-level size.
                    mipWidth  = int(128 * glm.pow(0.5, mip))
                    mipHeight = int(128 * glm.pow(0.5, mip))
                    glBindRenderbuffer(GL_RENDERBUFFER, self.rbo);
                    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, mipWidth, mipHeight)
                    glViewport(0, 0, mipWidth, mipHeight)

                    roughness = mip / (maxMipLevels - 1)
                    puregl.program.set_uniform(self.program, "roughness", roughness)

                    for i in range(6):
                        puregl.program.set_uniform(self.program, "viewMatrix", camera.views[i])
                        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, self.prefilter, mip)

                        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                        puregl.imdraw.cube(self.program, flip=True)

        return self.prefilter


class BRDFPass(RenderPass):
    """
    Generate a 2D LUT from the BRDF equations used
    """
    def __init__(self, width, height):
        super().__init__(width, height)
        self.program = None
        self.fbo = None
        self.brdflut = None #output texture

    def setup(self):
        # Create Shader
        self.program = puregl.program.create(*glsl.read('brdf'))
        
        # Create textures
        self.brdflut = glGenTextures(1)
        # pre-allocate enough memory for the LUT texture.
        glBindTexture(GL_TEXTURE_2D, self.brdflut)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RG16F, self.width, self.height, 0, GL_RG, GL_FLOAT, None);
        # be sure to set wrapping mode to GL_CLAMP_TO_EDGE
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # create fbo
        self.fbo = glGenFramebuffers(1)

        with puregl.fbo.bind(self.fbo):
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.brdflut, 0)
            assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

    def render(self):
        super().render()
        # re-configure capture framebuffer object and render screen-space quad with BRDF shader.
        with puregl.program.use(self.program):
            with puregl.fbo.bind(self.fbo):
                glViewport(0, 0, self.width, self.height)
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                puregl.imdraw.quad(self.program)

        return self.brdflut

if __name__ == "__main__":
    import glm
    from editor.render.graphics.viewer import Viewer
    from editor.render.graphics import Scene, Mesh, Geometry, Material
    import time, math

    viewer = Viewer(floating=True)
    environment_pass = EnvironmentPass(512,512)
    environment_image = assets.imread('hdri/Tropical_Beach_3k.hdr').astype(np.float32)
    environment_texture = None
    environment_cubemap = None
    irradiance_cubemap = None
    prefilter_cubemap = None
    brdf_texture = None

    irradiance_pass = IrradiancePass(32,32)
    prefilter_pass = PrefilterPass(128,128)
    brdf_pass = BRDFPass(512, 512)


    @viewer.on_setup
    def setup():
        global environment_texture, environment_cubemap, irradiance_cubemap, prefilter_cubemap, brdf_texture
        environment_texture = RenderPass.create_texture_from_data(environment_image)
        environment_pass.setup()
        irradiance_pass.setup()
        prefilter_pass.setup()
        brdf_pass.setup()
        # render passes
        camera360 = Camera360(transform=glm.mat4(1),
                              near=0.1, 
                              far=10)

        environment_cubemap = environment_pass.render(environment_texture, camera360)
        irradiance_cubemap = irradiance_pass.render(environment_cubemap, camera360)
        prefilter_cubemap = prefilter_pass.render(environment_cubemap, camera360)
        brdf_texture = brdf_pass.render()

    @viewer.on_draw
    def draw():
        global environment_texture, environment_cubemap, irradiance_cubemap, prefilter_cubemap, brdf_texture

        # render passes to screen
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        puregl.imdraw.cubemap(prefilter_cubemap, (0,0,viewer.width, viewer.height), viewer.camera.projection, viewer.camera.view)
    
        puregl.imdraw.texture(environment_texture, (  0, 0, 190, 190))
        puregl.imdraw.cubemap(environment_cubemap, (200, 0, 190, 190), viewer.camera.projection, viewer.camera.view)
        puregl.imdraw.cubemap(irradiance_cubemap,  (400, 0, 190, 190), viewer.camera.projection, viewer.camera.view)
        puregl.imdraw.cubemap(prefilter_cubemap,   (600, 0, 190, 190), viewer.camera.projection, viewer.camera.view)
        puregl.imdraw.texture(brdf_texture,        (800, 0, 190, 190))

    viewer.start(worker=False)
    print("- end of program -")


