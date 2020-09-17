from editor.render.graphics.passes.renderpass import RenderPass
from OpenGL.GL import *
from editor.render import puregl, glsl
import numpy as np

class DepthPass(RenderPass):
    def __init__(self, width, height):
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
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, self.width, self.height, 0, GL_RED, GL_FLOAT, None)

        # configure textures
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array([1, 1, 1, 1]))

        # create render buffer


        # Create fbo
        # ----------

        # configure fbo

        # attach textures

        # attach render buffers

        # cleanup

        # Create program
        # --------------

    def render(self, scene, camera):
        super()


if __name__ == "__main__":
    import glm
    from editor.render.graphics.viewer import Viewer
    from editor.render.graphics import Scene, Mesh, Geometry, Material

    cube = Mesh(transform=glm.translate(glm.mat4(1), (1, 0.5, 0.0)),
                geometry=Geometry(*puregl.geo.cube()),
                material=Material(albedo=(1, 0, 0),
                                  roughness=0.7,
                                  metallic=0.0))
    sphere = Mesh(transform=glm.translate(glm.mat4(1), (-1,0.5, 0.0)),
                  geometry=Geometry(*puregl.geo.sphere()),
                  material=Material(albedo=(0.04, 0.5, 0.8),
                                    roughness=0.2,
                                    metallic=1.0))
    plane = Mesh(transform=glm.translate(glm.mat4(1), (0, 0.0, 0.0)),
                 geometry=Geometry(*puregl.geo.plane()),
                 material=Material(albedo=(0.5, 0.5, 0.5),
                                   roughness=0.8,
                                   metallic=0.0))

    scene = Scene()
    scene.add_child(cube)
    scene.add_child(sphere)
    scene.add_child(plane)

    viewer = Viewer(floating=True)
    depth_pass = DepthPass(viewer.width, viewer.height)

    @viewer.on_setup
    def setup():
        scene._setup()
        print("setup geometry pass")
        depth_pass.setup()

    @viewer.on_draw
    def draw():
        # render passes
        depth_map = depth_pass.render(scene, viewer.camera)

        # render passes to screen
        glDisable(GL_DEPTH_TEST)
        puregl.imdraw.texture(depth_map, (0, 0, viewer.width, viewer.height), shuffle=(0, 1, 2, -1))

    viewer.start(worker=True)
    print("- end of program -")