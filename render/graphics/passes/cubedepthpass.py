from editor.render.graphics.passes.renderpass import RenderPass
from OpenGL.GL import *
from editor.render import puregl, glsl, imdraw
from editor.render.graphics import Mesh
from editor.render.graphics.cameras import Camera360
import numpy as np


class CubeDepthPass(RenderPass):
    def __init__(self, width, height, cull_face=GL_BACK):
        super().__init__(width, height, True, cull_face, None)
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
                glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i, 0, GL_DEPTH_COMPONENT, 
                    self.width, self.height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)

        # configure textures
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

        # Create fbo
        # ----------
        self.fbo = glGenFramebuffers(1)

        # configure fbo
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        # attach textures
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        glFramebufferTexture(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, self.texture, 0)

        # cleanup
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # Create program
        # --------------
        self.program = puregl.program.create(*glsl.read("point_shadow"))

    def render(self, objects: [Mesh], camera: Camera360):
        super().render()
        with puregl.fbo.bind(self.fbo), puregl.program.use(self.program):
            #set viewport
            glViewport(0,0,self.width, self.height)
            glClearColor(0,0,0,1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # configure shaders
            for i in range(6):
                puregl.program.set_uniform(self.program, "shadowMatrices[{}]".format(i), camera.projection * camera.views[i])
            puregl.program.set_uniform(self.program, "farPlane", float(camera.far))
            puregl.program.set_uniform(self.program, "lightPos", camera.position)

            # draw scene
            for mesh in objects:
                # transform
                puregl.program.set_uniform(self.program, "model", mesh.transform)

                # geometry
                mesh.geometry._draw(self.program)

        return self.texture


if __name__ == "__main__":
    import glm
    from editor.render.graphics.examples.viewer import Viewer
    from editor.render.graphics import Scene, Mesh, Geometry, Material
    import time, math

    scene = Scene.test_scene()

    viewer = Viewer(floating=True)
    cubedepth_pass = CubeDepthPass(1024,1024)

    @viewer.event
    def on_draw():
        # render passes
        pos = glm.vec3(math.cos(time.time()*2)*3, 1, 3)
        camera360 = Camera360(transform=glm.translate(glm.mat4(1), pos),
                              near=1, 
                              far=10)
        cubedepth_map = cubedepth_pass.render(scene.find_meshes(), camera360)

        # render passes to screen
        glDisable(GL_DEPTH_TEST)
        # imdraw.texture(depth_map, (0, 0, viewer.width, viewer.height), shuffle=(0,0,0,-1))
        imdraw.cubemap(cubedepth_map, (0,0,viewer.width, viewer.height), viewer.camera.projection, viewer.camera.view)
    viewer.start()
    print("- end of program -")