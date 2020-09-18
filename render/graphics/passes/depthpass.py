from editor.render.graphics.passes.renderpass import RenderPass
from OpenGL.GL import *
from editor.render import puregl, glsl
import numpy as np
import glm
from editor.render.graphics import Scene
from editor.render.graphics.cameras import PerspectiveCamera, OrthographicCamera

class DepthPass(RenderPass):
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
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, self.width, self.height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)

        # configure textures
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array([1, 1, 1, 1]))

        # cleanup
        glBindTexture(GL_TEXTURE_2D, 0)

        # Create fbo
        # ----------
        self.fbo = glGenFramebuffers(1)

        # configure fbo
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        # attach textures
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.texture, 0
        )

        # cleanup
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # Create program
        # --------------
        self.program = puregl.program.create(*glsl.read("simple_depth"))

    def render(self, scene: Scene, camera: (PerspectiveCamera, OrthographicCamera)):
        super().render()
        with puregl.fbo.bind(self.fbo), puregl.program.use(self.program):
            #set viewport
            glViewport(0,0,self.width, self.height)
            glClearColor(0,0,0,1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # configure shaders
            puregl.program.set_uniform(self.program, "projection", camera.projection)
            puregl.program.set_uniform(self.program, "view", camera.view)

            # draw scene
            for child in scene.children:
                # transform
                puregl.program.set_uniform(self.program, "model", child.transform)

                # material
                puregl.program.set_uniform(self.program, "albedo", glm.vec3(*child.material.albedo))
                puregl.program.set_uniform(self.program, "roughness", child.material.roughness)
                puregl.program.set_uniform(self.program, "metallic", child.material.metallic)

                # geometry
                child.geometry._draw(self.program)

        return self.texture


if __name__ == "__main__":
    from editor.render.graphics.viewer import Viewer
    from editor.render.graphics import Scene, Mesh, Geometry, Material

    scene = Scene.test_scene()

    viewer = Viewer(floating=True)
    viewer.camera.near = 1
    viewer.camera.far = 15
    depth_pass = DepthPass(viewer.width, viewer.height)

    @viewer.on_setup
    def setup():
        scene._setup()
        print("setup depth pass")
        depth_pass.setup()

    @viewer.on_draw
    def draw():
        # render passes
        depth_map = depth_pass.render(scene, viewer.camera)

        # render passes to screen
        glDisable(GL_DEPTH_TEST)
        puregl.imdraw.texture(depth_map, (0, 0, viewer.width, viewer.height), shuffle=(0,0,0,-1))

    viewer.start(worker=False)
    print("- end of program -")