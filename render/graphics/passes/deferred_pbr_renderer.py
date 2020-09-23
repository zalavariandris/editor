from editor.render.graphics import Scene
from editor.render.graphics.cameras import Camera360
from editor.render.graphics.lights import SpotLight, PointLight, DirectionalLight
import numpy as np
import glm

from editor.render.graphics.passes import GeometryPass, EnvironmentPass
from editor.render.graphics.passes import IrradiancePass, PrefilterPass, BRDFPass
from editor.render.graphics.passes import PBRLightingPass
from editor.render.graphics.passes import AddPass, TonemappingPass, ClampPass, GaussianblurPass

from editor.render.graphics.passes import RenderPass
from OpenGL.GL import *
from editor.render import puregl, glsl

from editor.render import assets
from editor.render.graphics import Mesh


class SkyboxPass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, True, GL_BACK)
        self.program = None
        self.texture = None
        self.fbo = None

    def setup(self):
        super().setup()
        # create program
        self.program = puregl.program.create(*glsl.read('skybox'))

        # create texture
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

        # create fbo
        self.fbo = glGenFramebuffers(1)
        with puregl.fbo.bind(self.fbo):
            glDrawBuffers(1, [GL_COLOR_ATTACHMENT0 + 0])
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0
            )

            # create depth+stencil buffer
            rbo = glGenRenderbuffers(1)
            glBindRenderbuffer(GL_RENDERBUFFER, rbo)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
            glBindRenderbuffer(GL_RENDERBUFFER, 0)

            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
            assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

    def render(self, environment, camera):
        super().render()
        with puregl.fbo.bind(self.fbo):
            # draw skybox
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LEQUAL)
            glDepthMask(GL_FALSE)
            glViewport(0, 0, self.width, self.height)
            with puregl.program.use(self.program) as prog:
                puregl.program.set_uniform(prog, 'projection', camera.projection)
                sky_view = glm.mat4(glm.mat3(camera.view));
                puregl.program.set_uniform(prog, 'view', sky_view)
                puregl.program.set_uniform(prog, 'cameraPos', camera.position)
                puregl.program.set_uniform(prog, 'skybox', 0)
                puregl.program.set_uniform(prog, 'groundProjection', True)
                glActiveTexture(GL_TEXTURE0 + 0)
                glBindTexture(GL_TEXTURE_CUBE_MAP, environment)
                puregl.imdraw.cube(prog, flip=True)

                glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
            glDepthMask(GL_TRUE)
        return self.texture


class DeferredPBRRenderer(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height)

        self.environment_image = assets.imread('hdri/Tropical_Beach_3k.hdr').astype(np.float32)
        self.environment_image = assets.to_linear(self.environment_image)

        # init passes
        self.geometry_pass = GeometryPass(self.width, self.height)
        self.environment_pass = EnvironmentPass(512, 512)
        self.irradiance_pass = IrradiancePass(32, 32)
        self.prefilter_pass = PrefilterPass(128, 128)
        self.brdf_pass = BRDFPass(512, 512)
        self.lighting_pass = PBRLightingPass(self.width, self.height)
        self.tonemapping_pass = TonemappingPass(self.width, self.height)
        self.clamp_pass = ClampPass(self.width, self.height)
        self.gaussianblur_pass = GaussianblurPass(self.width, self.height)
        self.add_pass = AddPass(self.width, self.height)

        self.skybox_pass = SkyboxPass(self.width, self.height)

        self.environment_texture = None
        self.environment_cubemap = None
        self.irradiance_cubemap = None
        self.prefilter_cubemap = None
        self.brdf_texture = None

    def setup(self):
        super().setup()
        self.environment_texture = RenderPass.create_texture_from_data(self.environment_image)

        # render passes
        camera360 = Camera360(transform=glm.mat4(1), near=0.1, far=15)

        self.environment_cubemap = self.environment_pass.render(self.environment_texture, camera360)
        self.irradiance_cubemap = self.irradiance_pass.render(self.environment_cubemap, camera360)
        self.prefilter_cubemap = self.prefilter_pass.render(self.environment_cubemap, camera360)
        self.brdf_texture = self.brdf_pass.render()

        from editor.render.graphics import Geometry
        self.ground_plane = Mesh(geometry=Geometry(*puregl.geo.plane()))

    def render(self, scene, camera):
        super().render()
        # Deferred rendering
        # ------------------
        # geometry
        gBuffer = self.geometry_pass.render(scene.find_meshes(), camera)

        # shadows
        for light in scene.find_lights():
            light.shadowmap.render(scene.find_meshes()+[self.ground_plane], light.camera)


        hdr_texture = self.lighting_pass.render(camera.position,
                                                scene.find_lights(),
                                                gBuffer,
                                                self.irradiance_cubemap,
                                                self.prefilter_cubemap,
                                                self.brdf_texture)

        # return hdr_texture

        # Forward rendering
        # -----------------
        self.skybox_pass.copy_buffer_from(self.geometry_pass, GL_DEPTH_BUFFER_BIT)
        self.skybox_pass.copy_buffer_from(self.lighting_pass, GL_COLOR_BUFFER_BIT)
        skybox_texture = self.skybox_pass.render(self.environment_cubemap, camera)
        # return skybox_texture
        # Postprocessing
        # --------------

        ldr_texture = self.tonemapping_pass.render(skybox_texture, exposure=0.0, gamma=2.2)
        return ldr_texture
        highlights_texture = self.clamp_pass.render(ldr_texture, minimum=0.9, maximum=1.0)
        # return ldr_texture
        blurred_highlights_texture = self.gaussianblur_pass.render(highlights_texture, iterations=4)
        # return blurred_highlights_texture
        with_bloom_texture = self.add_pass.render(ldr_texture, blurred_highlights_texture)

        return with_bloom_texture


if __name__ == "__main__":
    import logging
    from editor.render.graphics.window import Window
    logging.basicConfig(level=logging.DEBUG)

    if __name__ == "__main__":
        import glm

        from editor.render.graphics import Scene

        scene = Scene.test_scene()

        window = Window(floating=True)
        renderer = DeferredPBRRenderer(window.width, window.height)


        @window.on_draw
        def setup():
            beauty = renderer.render(scene, window.camera)
            puregl.imdraw.texture(beauty, (0, 0, window.width, window.height))


        window.start(worker=False)
        print("- end of program -")
