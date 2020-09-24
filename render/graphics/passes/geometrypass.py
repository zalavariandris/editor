from editor.render.graphics.passes.renderpass import RenderPass
from OpenGL.GL import *
from editor.render import puregl, glsl
import glm
from editor.render.graphics.cameras import PerspectiveCamera, OrthographicCamera
from editor.render.graphics import Mesh
from editor.render.assets import to_linear

class GeometryPass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, depth_test=True, cull_face=GL_BACK, blending=False)

        self.gPosition = self.gNormal = self.gAlbedo = self.gEmission = self.gRoughness = self.gMetallic = None
        self.fbo = None
        self.program = None

    def setup(self):
        super().setup()
        # Create textures
        # ---------------
        self.gPosition, self.gNormal, self.gAlbedo, self.gEmission, self.gRoughness, self.gMetallic = glGenTextures(6)
        
        # define textures
        glBindTexture(GL_TEXTURE_2D, self.gPosition)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gNormal)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gAlbedo)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gEmission)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gRoughness)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, self.width, self.height, 0, GL_RED, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gMetallic)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, self.width, self.height, 0, GL_RED, GL_FLOAT, None)
        
        # configure textures
        for tex in [self.gPosition, self.gNormal, self.gAlbedo, self.gEmission, self.gRoughness, self.gMetallic]:
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D, 0)

        # create render buffer
        self.gDepth = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.gDepth)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, self.width, self.height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

        # Create fbo
        # ----------
        self.fbo = glGenFramebuffers(1)

        # configure fbo
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glDrawBuffers(6, [GL_COLOR_ATTACHMENT0+i for i in range(6)])

        # attach textures
        for i, tex in enumerate([self.gPosition, self.gNormal, self.gAlbedo, self.gEmission, self.gRoughness, self.gMetallic]):
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0+i, GL_TEXTURE_2D, tex, 0
            )

        # attach render buffers
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.gDepth, 0
        )

        # cleanup
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # Create program
        # --------------
        self.program = puregl.program.create(*glsl.read("graphics/geometry"))

    def render(self, objects: [Mesh], camera: (PerspectiveCamera, OrthographicCamera)):
        super().render()

        with puregl.fbo.bind(self.fbo), puregl.program.use(self.program):
            glViewport(0,0, self.width, self.height)
            glClearColor(0,0,0,0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # set camera
            puregl.program.set_uniform(self.program, "projection", camera.projection)
            puregl.program.set_uniform(self.program, "view", camera.view)

            # draw scene
            for mesh in objects:
                # transform
                puregl.program.set_uniform(self.program, "model", mesh.transform)

                # material
                puregl.program.set_uniform(self.program, "albedo", to_linear(glm.vec3(*mesh.material.albedo)))
                puregl.program.set_uniform(self.program, "emission", to_linear(glm.vec3(*mesh.material.emission)))
                puregl.program.set_uniform(self.program, "roughness", mesh.material.roughness)
                puregl.program.set_uniform(self.program, "metallic", mesh.material.metallic)

                # geometry
                mesh.geometry._draw(self.program)

        return self.gPosition, self.gNormal, self.gAlbedo, self.gEmission, self.gRoughness, self.gMetallic

            
if __name__ == "__main__":
    import glm
    from editor.render.graphics.window import Window
    from editor.render.graphics import Scene, Mesh, Geometry, Material

    cube = Mesh(transform=glm.translate(glm.mat4(1), (1, 0.5, 0.0)),
                geometry=Geometry(*puregl.geo.cube()),
                material=Material(albedo=(1, 0, 0),
                                  emission=(0,0,0),
                                  roughness=0.7,
                                  metallic=0.0))
    sphere = Mesh(transform=glm.translate(glm.mat4(1), (-1,0.5, 0.0)),
                  geometry=Geometry(*puregl.geo.sphere()),
                  material=Material(albedo=(0.04, 0.5, 0.8),
                                    emission=(0,0,0),
                                    roughness=0.2,
                                    metallic=1.0))
    plane = Mesh(transform=glm.translate(glm.mat4(1), (0, 0.0, 0.0)),
                 geometry=Geometry(*puregl.geo.plane()),
                 material=Material(albedo=(0.5, 0.5, 0.5),
                                   emission=(0,0,0),
                                   roughness=0.8,
                                   metallic=0.0))

    scene = Scene()
    scene.add_child(cube)
    scene.add_child(sphere)
    scene.add_child(plane)

    viewer = Window(floating=True)
    viewer.camera.far = 10
    viewer.camera.near = 1
    geometry_pass = GeometryPass(viewer.width, viewer.height)

    @viewer.on_setup
    def setup():
        logging.debug("GL_MAX_COLOR_ATTACHMENTS:", glGetIntegerv(GL_MAX_COLOR_ATTACHMENTS ))
        scene._setup()
        geometry_pass.setup()

    @viewer.on_draw
    def draw():
        # render passes
        gBuffer = geometry_pass.render(scene, viewer.camera)
        gPosition, gNormal, gAlbedo, gEmission, gRoughness, gMetallic = gBuffer

        # render passes to screen
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        # glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.5,0.5,0.5,0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        checkerboard_program = puregl.program.create(
            """#version 330 core
            layout (location=0) in vec3 position;
            layout (location=1) in vec2 uv;
            out vec2 TexCoords;
            void main(){
                TexCoords = uv;
                gl_Position = vec4(position,1.0);
            }
            """,
            """#version 330 core
            in vec2 TexCoords;
            out vec4 FragColor;
            uniform float size;
            uniform vec2 viewportSize;
            float checker(vec2 uv, vec2 repeats){
                float cx = floor(repeats.x * uv.x);
                float cy = floor(repeats.y * uv.y);
                float result = mod(cx + cy, 2.0);
                return sign(result);
            }

            void main(){
                vec4 colorA = vec4(0.6,0.6,0.6,0.5);
                vec4 colorB = vec4(0.4,0.4,0.4,0.5);
                FragColor = mix(colorA, colorB, checker(TexCoords, viewportSize/size));
            }
            """)
        with puregl.program.use(checkerboard_program):
            puregl.program.set_uniform(checkerboard_program, "viewportSize", (viewer.width, viewer.height))
            puregl.program.set_uniform(checkerboard_program, "size", 8.0)
            puregl.imdraw.quad(checkerboard_program)

        puregl.imdraw.texture(gPosition, (20, 20, viewer.width-40, viewer.height-40), shuffle=(0, 1, 2, 3))

        #
        puregl.imdraw.texture(gPosition, (0,0,190, 190), shuffle=(0,1,2,3))
        puregl.imdraw.texture(gNormal, (200,0,190, 190), shuffle=(0,1,2,-1))
        puregl.imdraw.texture(gAlbedo, (400,0,190, 190), shuffle=(0,1,2,-1))
        puregl.imdraw.texture(gEmission, (600,0,190, 190))
        puregl.imdraw.texture(gRoughness, (800,0,190, 190), shuffle=(0,0,0,-1))
        puregl.imdraw.texture(gMetallic, (1000,0,190, 190), shuffle=(0,0,0,-1))

        puregl.imdraw.texture(geometry_pass.gDepth, (  0, 200, 190, 190), shuffle=(0, 0, 0, -1))

    viewer.start(worker=True)
    print("- end of program -")
