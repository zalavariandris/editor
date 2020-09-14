from OpenGL.GL import *
import glm
import numpy as np
from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program, texture, fbo
from editor.render import glsl
from editor.render import assets
from editor.render.graphics.cameras import PerspectiveCamera, OrthographicCamera

from editor.render.graphics.lights import DirectionalLight, Spotlight, Pointlight

from geometrypass import GeometryPass
from depthpass import DepthPass
from cubedepthpass import CubeDepthPass
from environmentpass import EnvironmentPass
from iblpass import IrradiancePass, PrefilterPass, BRDFPass
from lightingpass import LightingPass
from tonemappingpass import TonemappingPass

import logging

logging.basicConfig(filename=None, level=logging.DEBUG, format='%(levelname)s:%(module)s.%(funcName)s: %(message)s')

# create scene
dirlight = DirectionalLight(direction=glm.vec3(5, -8, -3),
                            color=glm.vec3(1.0) * 1.0,
                            position=glm.vec3(-5, 8, 3),
                            radius=5.0,
                            near=1.0,
                            far=30)

spotlight = Spotlight(position=glm.vec3(-2, 5.1, -10),
                      direction=glm.vec3(2, -5.1, 10),
                      color=glm.vec3(0.2, 0.18, 0.7) * 150,
                      fov=30.0,
                      near=1.0,
                      far=30.0)

pointlight = Pointlight(position=glm.vec3(5, 2, 4),
                        color=glm.vec3(1, 0.7, 0.1) * 10,
                        near=1.0,
                        far=8.0)


class Viewer:
    def __init__(self, scene):
        # window
        self.width = 1024
        self.height = 768
        self.window = GLFWViewer(self.width, self.height, (0.2, 0.2, 0.2, 1.0))
        self.camera = PerspectiveCamera(glm.inverse(self.window.view_matrix), glm.radians(60), self.width / self.height,
                                        1, 30)
        self.scene = scene

        # assets
        self.environment_image = assets.imread('hdri/Tropical_Beach_3k.hdr')
        self.environment_image = assets.to_linear(self.environment_image)

        # render passes
        self.environment_pass = EnvironmentPass(512, 512)
        self.irradiance_pass = IrradiancePass(32, 32)
        self.prefilter_pass = PrefilterPass()
        self.brdf_pass = BRDFPass(512, 512)
        self.tonemapping_pass = TonemappingPass(self.width, self.height)

        self.geometry_pass = GeometryPass(self.width, self.height, self.draw_scene)
        self.lighting_pass = LightingPass(self.width, self.height, lights=[dirlight, spotlight, pointlight])

        dirlight.shadowpass = DepthPass(1024, 1024, GL_FRONT, self.draw_scene)
        spotlight.shadowpass = DepthPass(1024, 1024, GL_FRONT, self.draw_scene)
        pointlight.shadowpass = CubeDepthPass(512, 512, GL_FRONT, near=1, far=15, draw_scene=self.draw_scene)

    def setup(self):
        # glEnable(GL_PROGRAM_POINT_SIZE)

        # Render passes
        # -------------

        # geometry
        self.geometry_pass.setup()

        # environment
        self.environment_tex = texture.create(self.environment_image, 0, GL_RGB,
                                              wrap_s=GL_CLAMP_TO_EDGE,
                                              wrap_t=GL_CLAMP_TO_EDGE,
                                              min_filter=GL_LINEAR,
                                              mag_filter=GL_LINEAR)
        self.environment_pass.texture = self.environment_tex
        self.environment_pass.setup()
        self.environment_pass.render()

        # ibl
        self.prefilter_pass.setup()
        self.prefilter_pass.environment = self.environment_pass.cubemap
        self.prefilter_pass.render()

        self.irradiance_pass.setup()
        self.irradiance_pass.environment = self.environment_pass.cubemap
        self.irradiance_pass.render()

        self.brdf_pass.setup()
        self.brdf_pass.render()

        # shadows
        dirlight.shadowpass.setup()
        spotlight.shadowpass.setup()
        pointlight.shadowpass.setup()

        # lighting
        self.lighting_pass.setup()
        self.lighting_pass.irradiance = self.irradiance_pass.irradiance
        self.lighting_pass.prefilter = self.prefilter_pass.prefilter
        self.lighting_pass.brdf = self.brdf_pass.brdflut

        # setup forward rendering
        self.forward_fbo = glGenFramebuffers(1)
        with fbo.bind(self.forward_fbo):
            glDrawBuffers(1, [GL_COLOR_ATTACHMENT0 + 0])
            self.forward_texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.forward_texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.forward_texture, 0
            )
            glBindTexture(GL_TEXTURE_2D, 0)

            # create depth+stencil buffer
            rbo = glGenRenderbuffers(1)
            glBindRenderbuffer(GL_RENDERBUFFER, rbo)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
            glBindRenderbuffer(GL_RENDERBUFFER, 0)

            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
            assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

        self.skybox_program = program.create(*glsl.read('skybox'))

        # tonemapping
        self.tonemapping_pass.setup()

    def resize(self):
        with self.window:
            pass

    def draw_scene(self, prog):
        for child in self.scene.children:
            program.set_uniform(prog, 'albedo', child['material']['albedo'])
            program.set_uniform(prog, 'model', child['transform'])
            program.set_uniform(prog, 'model', child['transform'])
            child['geometry'](prog)

    def render(self):
        # Animate
        # -------
        import math, time
        spotlight.position = glm.vec3(math.cos(time.time() * 3) * 4, 0.3, -4)
        spotlight.direction = -spotlight.position
        pointlight.position = glm.vec3(math.cos(time.time()) * 4, 4, math.sin(time.time()) * 4)
        self.camera.transform = glm.inverse(self.window.view_matrix)

        # Render passes
        # -------------
        ## Geometry
        self.geometry_pass.camera = self.camera  # window.projection_matrix, window.view_matrix
        self.geometry_pass.render()

        ## Shadowmaps
        dirlight.shadowpass.camera = dirlight.camera
        dirlight.shadowpass.render()
        spotlight.shadowpass.camera = spotlight.camera
        spotlight.shadowpass.render()
        pointlight.shadowpass.position = pointlight.position
        pointlight.shadowpass.render()

        ## Lighting
        self.lighting_pass.cameraPos = self.camera.position
        self.lighting_pass.gPosition = self.geometry_pass.gPosition
        self.lighting_pass.gNormal = self.geometry_pass.gNormal
        self.lighting_pass.gAlbedoSpecular = self.geometry_pass.gAlbedoSpecular
        self.lighting_pass.gRoughness = self.geometry_pass.gRoughness
        self.lighting_pass.gMetallic = self.geometry_pass.gMetallic
        self.lighting_pass.gEmissive = self.geometry_pass.gEmissive
        self.lighting_pass.render()

        ## Forward rendering

        #  - Copy depth from geometry pass
        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.geometry_pass.gBuffer)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.forward_fbo)  # write to default framebuffer
        glBlitFramebuffer(
            0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_DEPTH_BUFFER_BIT, GL_NEAREST
        );
        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.lighting_pass.fbo)
        glBlitFramebuffer(
            0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST
        );
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)

        with fbo.bind(self.forward_fbo):
            # draw skybox
            glViewport(0, 0, self.width, self.height)
            with program.use(self.skybox_program) as prog:
                program.set_uniform(prog, 'projection', self.camera.projection)
                sky_view = glm.mat4(glm.mat3(self.camera.view));
                program.set_uniform(prog, 'view', sky_view)
                program.set_uniform(prog, 'cameraPos', self.camera.position)
                program.set_uniform(prog, 'skybox', 0)
                program.set_uniform(prog, 'groundProjection', True)
                glActiveTexture(GL_TEXTURE0 + 0)
                glBindTexture(GL_TEXTURE_CUBE_MAP, self.environment_pass.cubemap)
                imdraw.cube(prog, flip=True)

                glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
            glDepthMask(GL_TRUE)

        ## Tonemapping
        self.tonemapping_pass.hdrimage = self.lighting_pass.beauty
        self.tonemapping_pass.exposure = 0.0
        self.tonemapping_pass.gamma = 2.2
        self.tonemapping_pass.render()

        # Render to screen
        # ----------------
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)

        # draw to screen
        imdraw.texture(self.tonemapping_pass.ldrimage, (0, 0, self.width, self.height))

        # debug
        imdraw.texture(self.geometry_pass.gPosition, (0, 0, 90, 90))
        imdraw.texture(self.geometry_pass.gNormal, (100, 0, 90, 90))
        imdraw.texture(self.geometry_pass.gAlbedoSpecular, (200, 0, 90, 90), shuffle=(0, 1, 2, -1))
        imdraw.texture(self.geometry_pass.gAlbedoSpecular, (300, 0, 90, 90), shuffle=(3, 3, 3, -1))
        imdraw.texture(self.geometry_pass.gRoughness, (400, 0, 90, 90), shuffle=(0, 0, 0, -1))
        imdraw.texture(self.geometry_pass.gMetallic, (500, 0, 90, 90), shuffle=(0, 0, 0, -1))

        imdraw.texture(dirlight.shadowpass.texture, (0, 100, 90, 90), shuffle=(0, 0, 0, -1))
        imdraw.texture(spotlight.shadowpass.texture, (100, 100, 90, 90), shuffle=(0, 0, 0, -1))
        imdraw.cubemap(pointlight.shadowpass.cubemap, (200, 100, 90, 90), self.window.projection_matrix,
                       self.window.view_matrix)

        imdraw.texture(self.environment_tex, (0, 200, 90, 90))
        imdraw.cubemap(self.environment_pass.cubemap, (100, 200, 90, 90), self.window.projection_matrix,
                       self.window.view_matrix)

        imdraw.cubemap(self.irradiance_pass.irradiance, (200, 200, 90, 90), self.window.projection_matrix,
                       self.window.view_matrix)
        imdraw.cubemap(self.prefilter_pass.prefilter, (300, 200, 90, 90), self.window.projection_matrix,
                       self.window.view_matrix)
        imdraw.texture(self.brdf_pass.brdflut, (400, 200, 90, 90))

        imdraw.texture(self.lighting_pass.beauty, (0, 300, 90, 90))

        # swap buffers
        # ------------
        self.window.swap_buffers()
        GLFWViewer.poll_events()

    def start(self):
        with self.window:
            self.setup()
            while not self.window.should_close():
                self.render()


class Scene:
    def draw(self, prog):
        # draw cube
        model_matrix = glm.translate(glm.mat4(1), (-1, 0.5, 0))
        program.set_uniform(prog, 'model', model_matrix)
        program.set_uniform(prog, 'albedo', glm.vec3(0.9, 0.1, 0))
        program.set_uniform(prog, 'roughness', 0.1)
        program.set_uniform(prog, 'metalness', 0.0)

        imdraw.cube(prog)

        # draw sphere
        model_matrix = glm.translate(glm.mat4(1), (1, 0.5, 0))
        program.set_uniform(prog, 'model', model_matrix)
        imdraw.sphere(prog)

        # draw ground-plane
        model_matrix = glm.translate(glm.mat4(1), (0, 0.0, 0))
        program.set_uniform(prog, 'model', model_matrix)
        imdraw.plane(prog)

    @property
    def children(self):
        return [
            {
                'transform': glm.translate(glm.mat4(1), (-1, 0.5, 0)),
                'material': {
                    'albedo': glm.vec3(0.9, 0.3, 0),
                    'roughness': 0.3,
                    'metallic': 0.0,
                    'ao': 1.0
                },
                'geometry': imdraw.cube
            },
            {
                'transform': glm.translate(glm.mat4(1), (1, 0.5, 0)),
                'material': {
                    'albedo': glm.vec3(0.0, 0.7, 0.9),
                    'roughness': 0.3,
                    'metallic': 1.0,
                    'ao': 1.0
                },
                'geometry': imdraw.sphere
            },
            {
                'transform': glm.translate(glm.mat4(1), (0, 0.0, 0)),
                'material': {
                    'albedo': glm.vec3(0.5),
                    'roughness': 0.3,
                    'metallic': 0.0,
                    'ao': 1.0
                },
                'geometry': imdraw.plane
            }
        ]


if __name__ == "__main__":
    viewer = Viewer(scene=Scene())
    viewer.start()
