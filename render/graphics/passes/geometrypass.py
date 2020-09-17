from editor.render.graphics.passes.renderpass import RenderPass
from OpenGL.GL import *
from editor.render import puregl, glsl
import glm

class GeometryPass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, depth_test=True, cull_face=GL_BACK, blending=None)
        self.gPosition = self.gNormal = self.gAlbedo = self.gRoughness = self.gMetallic = self.gEmissive = None
        self.fbo = None
        self.program = None

    def setup(self):
        # Create textures
        # ---------------
        self.gPosition, self.gNormal, self.gAlbedo, self.gRoughness, self.gMetallic, self.gEmissive = glGenTextures(6)
        
        # define textures
        glBindTexture(GL_TEXTURE_2D, self.gPosition)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gNormal)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gAlbedo)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gEmissive)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gRoughness)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, self.width, self.height, 0, GL_RED, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gMetallic)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, self.width, self.height, 0, GL_RED, GL_FLOAT, None)
        
        # configure textures
        for tex in [self.gPosition, self.gNormal, self.gAlbedo, self.gRoughness, self.gMetallic, self.gEmissive]:
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D, 0)

        # create render buffer
        rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        # Create fbo
        # ----------
        self.fbo = glGenFramebuffers(1)

        # configure fbo
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glDrawBuffers(6, [GL_COLOR_ATTACHMENT0+i for i in range(6)])

        # attach textures
        for i, tex in enumerate([self.gPosition, self.gNormal, self.gAlbedo, self.gRoughness, self.gMetallic, self.gEmissive]):
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0+i, GL_TEXTURE_2D, tex, 0
            )

        # attach render buffers
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)

        # cleanup
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # Create program
        # --------------
        self.program = puregl.program.create(*glsl.read("deferred_geometry"))
        
    def resize(self, width, height):
        pass

    def render(self, scene, camera):
        super().render()

        with puregl.fbo.bind(self.fbo), puregl.program.use(self.program):
            glViewport(0,0, self.width, self.height)
            glClearColor(0,0,0,1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # set camera
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

        return self.gPosition, self.gNormal, self.gAlbedo, self.gEmissive, self.gRoughness, self.gMetallic

            
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
    geometry_pass = GeometryPass(viewer.width, viewer.height)

    @viewer.on_setup
    def setup():
        scene._setup()
        print("setup geometry pass")
        geometry_pass.setup()

    @viewer.on_draw
    def draw():
        # render passes
        gBuffer = geometry_pass.render(scene, viewer.camera)
        gPosition, gNormal, gAlbedo, gEmissive, gRoughness, gMetallic = gBuffer

        # render passes to screen
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        puregl.imdraw.texture(gPosition, (0, 0, viewer.width, viewer.height), shuffle=(0, 1, 2, -1))

        puregl.imdraw.texture(gPosition, (0,0,190, 190), shuffle=(0,1,2,-1))
        puregl.imdraw.texture(gNormal, (200,0,190, 190), shuffle=(0,1,2,-1))
        puregl.imdraw.texture(gAlbedo, (400,0,190, 190), shuffle=(0,1,2,-1))
        puregl.imdraw.texture(gEmissive, (600,0,190, 190))
        puregl.imdraw.texture(gRoughness, (800,0,190, 190), shuffle=(0,0,0,-1))
        puregl.imdraw.texture(gMetallic, (1000,0,190, 190), shuffle=(0,0,0,-1))

    viewer.start(worker=True)
    print("- end of program -")
