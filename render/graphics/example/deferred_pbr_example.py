from OpenGL.GL import *
import glm
import numpy as np
from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program, texture, fbo
from editor.render import glsl
from editor.render import assets
from editor.render.graphics import PerspectiveCamera, OrthographicCamera
from editor.render.graphics import DirectionalLight, Spotlight, Pointlight
from editor.render.graphics import Mesh, Scene, Geometry, Material

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


        self.geometry_pass = GeometryPass(self.width, self.height, self.draw_scene_for_geometry)
        dirlight.shadowpass = DepthPass(1024, 1024, GL_FRONT, self.draw_scene_for_shadows)
        spotlight.shadowpass = DepthPass(1024, 1024, GL_FRONT, self.draw_scene_for_shadows)
        pointlight.shadowpass = CubeDepthPass(512, 512, GL_FRONT, near=1, far=15, draw_scene=self.draw_scene_for_shadows)

        self.lighting_pass = LightingPass(self.width, self.height, lights=[dirlight, spotlight, pointlight])

    def get_geometry_buffer(self, mesh):
        try:
            geometry_buffers = self._geometry_buffers
        except AttributeError:
            geometry_buffers = dict()
            self._geometry_buffers = geometry_buffers

        try:
            geo_buffer = geometry_buffers[mesh]
        except KeyError:
            logging.debug("create goemetry buffer for {}".format(mesh))
            positions = mesh.geometry.positions
            normals = mesh.geometry.normals
            uvs = mesh.geometry.uvs
            indices = mesh.geometry.indices

            # create vertex buffers
            pos_vbo, uv_vbo, normal_vbo = glGenBuffers(3)

            glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
            glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
            glBufferData(GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, normal_vbo)
            glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

            # create vertex array
            vao = glGenVertexArrays(1)

            # create element buffer
            ebo = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

            # link buffer to geometry
            geo_buffer = (vao, ebo, pos_vbo, uv_vbo, normal_vbo, indices.size)
            geometry_buffers[mesh] = geo_buffer

        return geo_buffer

    def draw_scene_for_geometry(self, prog):
        import ctypes
        for child in self.scene.children:
            # set uniforms
            program.set_uniform(prog, 'model', child.transform)
            program.set_uniform(prog, 'albedo', child.material.albedo)
            program.set_uniform(prog, 'roughness', child.material.roughness)
            program.set_uniform(prog, 'metallic', child.material.metallic)

            # set attributes
            vao, ebo, pos_vbo, uv_vbo, normal_vbo, count = self.get_geometry_buffer(child)
            glBindVertexArray(vao)
            position_location = glGetAttribLocation(prog, 'position')
            glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
            glVertexAttribPointer(position_location, 3, GL_FLOAT, False, 0, ctypes.c_void_p(0))
            glEnableVertexAttribArray(position_location)

            uv_location = glGetAttribLocation(prog, 'uv')
            if uv_location is not -1:
                glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
                glVertexAttribPointer(uv_location, 2, GL_FLOAT, False, 0, ctypes.c_void_p(0))
                glEnableVertexAttribArray(uv_location)

            normal_location = glGetAttribLocation(prog, 'normal')
            if normal_location is not -1:
                glBindBuffer(GL_ARRAY_BUFFER, normal_vbo)
                glVertexAttribPointer(normal_location, 3, GL_FLOAT, False, 0, ctypes.c_void_p(0))
                glEnableVertexAttribArray(normal_location)

            # draw geometry
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
            glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)

            # cleanup bindings
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindVertexArray(0)

    def draw_scene_for_shadows(self, prog):
        for child in self.scene.children:
            # set uniforms
            program.set_uniform(prog, 'model', child.transform)

            # set attributes
            vao, ebo, pos_vbo, uv_vbo, normal_vbo, count = self.get_geometry_buffer(child)
            glBindVertexArray(vao)
            position_location = glGetAttribLocation(prog, 'position')
            glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
            glVertexAttribPointer(position_location, 3, GL_FLOAT, False, 0, ctypes.c_void_p(0))
            glEnableVertexAttribArray(position_location)

            # draw geometry
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
            glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)

            # cleanup bindings
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindVertexArray(0)

    def setup(self):
        logging.debug("setup viewer")
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


if __name__ == "__main__":
    scene = Scene()
    cube = Mesh(transform=glm.translate(glm.mat4(1), (-1, 0.5, 0)),
                material=Material(albedo=glm.vec3(0.9, 0.04, 0.04),
                                  roughness=0.6,
                                  metallic=0.0,
                                  ao=1.0),
                geometry=Geometry.cube())

    sphere = Mesh(transform=glm.translate(glm.mat4(1), (1, 0.5, 0)),
                  material=Material(albedo=glm.vec3(0.04, 0.7, 0.9),
                                    roughness=0.2,
                                    metallic=1.0,
                                    ao=1.0),
                  geometry=Geometry.sphere())

    plane = Mesh(transform=glm.translate(glm.mat4(1), (0, 0.0, 0)),
                 material=Material(albedo=glm.vec3(0.5),
                                   roughness=0.3,
                                   metallic=0.0,
                                   ao=1.0),
                 geometry=Geometry.plane())

    scene.add_child(cube)
    scene.add_child(sphere)
    scene.add_child(plane)
    viewer = Viewer(scene=scene)
    viewer.start()
