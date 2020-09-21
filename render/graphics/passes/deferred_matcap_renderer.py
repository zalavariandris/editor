from OpenGL.GL import *
import numpy as np
from editor.render import puregl, assets
from editor.render.graphics.passes import RenderPass, GeometryPass
from editor.render.graphics import Mesh
import logging
logging.basicConfig(level=logging.DEBUG)


class MatcapLightingPass(RenderPass):
    def __init__(self, width, height, depth_test=False, cull_face=False, blending=False, seamless_cubemap=False):
        super().__init__(width, height, depth_test, cull_face, blending, seamless_cubemap)
        self.program = None
        self.fbo = None
        self.texture = None

    def setup(self):
        super().setup()
        # create program
        # --------------
        self.program = puregl.program.create(
            """#version 330 core
            layout (location=0) in vec3 position;
            layout (location=1) in vec2 uv;
            layout (location=2) in vec3 normal;
            out vec2 TexCoords;
            void main(){
                TexCoords = uv;
                gl_Position = vec4(position, 1.0);
            }
            """,
            """#version 330 core
            uniform sampler2D gPosition;
            uniform sampler2D gNormal;
            uniform sampler2D matcap;

            uniform vec2 viewportSize;
            in vec2 TexCoords;
            out vec4 FragColor;
            uniform vec3 camPos;
            void main(){
                vec3 normal = normalize(texture(gNormal, TexCoords).rgb);
                vec3 position = texture(gPosition, TexCoords).rgb;
                vec3 eye = normalize(camPos - position);
                vec3 R = reflect(eye, normal);

                float m = 2. * sqrt( pow( R.x, 2. ) + pow( R.y, 2. ) + pow( R.z + 1., 2. ) );
                vec2 vN = R.xy / m + 0.5;

                vec3 color = texture( matcap, vN ).rgb;
                FragColor = vec4(color, 1.0);
            }
            """
        )

        # create texture(s)
        # ----------------
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D, 0)

        # create fbo
        # ----------
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glDrawBuffers(1, [GL_COLOR_ATTACHMENT0 + 0])
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0 + 0, GL_TEXTURE_2D, self.texture, 0
        )
        glBindTexture(GL_TEXTURE_2D, 0)

        # create render buffers for depth and stencil
        rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def render(self, matcap, gPosition, gNormal, camera):
        super().render()
        with puregl.fbo.bind(self.fbo), puregl.program.use(self.program):
            # clear fbo
            glViewport(0, 0, self.width, self.height)
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # configure shader
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, gPosition)
            puregl.program.set_uniform(self.program, "gPosition", 0)
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, gNormal)
            puregl.program.set_uniform(self.program, "gNormal", 1)
            glActiveTexture(GL_TEXTURE2)
            glBindTexture(GL_TEXTURE_2D, matcap)
            puregl.program.set_uniform(self.program, "matcap", 2)
            puregl.program.set_uniform(self.program, "camPos", camera.position)

            # draw
            puregl.imdraw.quad(self.program)
            glBindTexture(GL_TEXTURE_2D, 0)
        return self.texture


class DeferredMatcapRenderer(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, True, GL_BACK)
        self.geometry_pass = GeometryPass(self.width, self.height)
        self.matcap_pass =   MatcapLightingPass(self.width, self.height)
        self.matcap_image = assets.imread("matcap/jeepster_skinmat2.jpg").astype(np.float32)[..., :3]/255
        self.matcap_texture = None

    def setup(self):
        super().setup()
        self.matcap_texture = RenderPass.create_texture_from_data(self.matcap_image)

    def render(self, scene, camera):
        super().render()
        gBuffer = self.geometry_pass.render(scene.find_all(lambda obj: isinstance(obj, Mesh)), camera)
        beauty = self.matcap_pass.render(self.matcap_texture, gBuffer[0], gBuffer[1], camera)
        return beauty


if __name__ == "__main__":
    import glm
    from editor.render.graphics.window import Window
    from editor.render.graphics import Scene, Mesh, Geometry, Material

    # create scene
    scene = Scene()
    mesh = Mesh(transform=glm.mat4(1),
                material=Material(albedo=(0, 0, 0),
                                  emission=(0, 0, 0),
                                  roughness=0.0,
                                  metallic=0.0),
                geometry=Geometry(*puregl.geo.sphere()))
    scene.add_child(mesh)

    # create and start viewer
    window = Window(floating=True)
    renderer = DeferredMatcapRenderer(window.width, window.height)

    @window.on_setup
    def setup():
        scene.setup()
        renderer.setup()

    @window.on_draw
    def draw():
        beauty = renderer.render(scene, window.camera)
        puregl.imdraw.texture(beauty, (0, 0, window.width, window.height))
    window.start(worker=False)
    print("- end of program -")
